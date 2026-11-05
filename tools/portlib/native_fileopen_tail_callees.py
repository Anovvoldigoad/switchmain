"""Exact SHA-pinned original native FileOpen tail 8-callsite transitive evidence.

Classifies all eight *reachable* BL/BLR sites in the bounded tail function,
recovers direct targets and (where present) original PLT/GOT symbol
relocations, and computes intraprocedural W0 reaching definitions at the
local return. No symbolic heap, CRI semantics, callee side effects, or
calling-convention/lifecycle proof is implied by this static investigation.
"""
import hashlib
import struct
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_cpk_indirect import adrp_ldr_slot
from .native_fileopen_tail import TAIL_TARGET, TAIL_WINDOW_SIZE, inspect as inspect_tail
from .native_fileopen_callees import _decode_window, _callee_walk
from .native_fileopen_returns import _trace
from .native_fileopen_import import _read_image, _tags, _scan_relocations, _symbol
from .nso_profile import segments

EXPECTED_SITES=(0x115EC18,0x115EC28,0x115EC48,0x115EC68,
                0x115EC84,0x115EC88,0x115EC90,0x115EC94)
MAX_CALLEE_WINDOW=0x140
TRANSCRIPT_BYTES=0x50
RET_SITE=0x115ECA8

def _one(text,pc):
    cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    cs.detail=True
    ins=list(cs.disasm(text[pc:pc+4],pc))
    if len(ins)!=1 or ins[0].size!=4:
        raise ValueError("Undecodable exact main native call word "+hex(pc))
    return ins[0]

def _plt_import(text,mem,tags,target):
    """Only resolve four-instruction AArch64 PLT X16/X17 thunk shape.

    Returns None for ordinary code; an unresolved PLT slot is not a name.
    """
    if target<0 or target+16>len(text):
        return None
    a,b,c,d=[_one(text,target+i*4) for i in range(4)]
    if not (a.mnemonic=="adrp" and a.op_str.startswith("x16, ") and
            b.mnemonic=="ldr" and b.op_str.startswith("x17, [x16, ") and
            c.mnemonic=="add" and c.op_str.startswith("x16, x16, ") and
            d.mnemonic=="br" and d.op_str=="x17"):
        return None
    first,second=struct.unpack_from("<2I",text,target)
    slot=adrp_ldr_slot(first,second,target)
    if slot is None:
        raise ValueError("PLT sequence with unresolved ADRP/GOT slot")
    hits=_scan_relocations(mem,tags,slot)
    if len(hits)!=1:
        raise ValueError("Native GOT slot has no unique original import relocation")
    rel=hits[0]
    if rel["type_name"]!="R_AARCH64_JUMP_SLOT":
        raise ValueError("Original GOT slot is not a JUMP_SLOT")
    return {
        "got_slot":hex(slot),
        "relocation":rel,
        "symbol":_symbol(mem,tags,rel["symbol_index"]),
        "original_import_name_only_not_native_implementation":True,
    }

def _callee_report(text,mem,tags,at):
    ins=_one(text,at)
    orig_word=text[at:at+4]
    if ins.mnemonic not in ("bl","blr","blraa","blrab"):
        raise ValueError("Original tail expected CALL changed at "+hex(at))
    item={
        "site":hex(at),"word_le":orig_word.hex(),
        "instruction":(ins.mnemonic+" "+ins.op_str).strip(),
        "fallthrough":hex(at+4),
        "direct_target":None,"target_first_words":[],
        "plt_import":None,
        "indirect_call_unresolved":ins.mnemonic!="bl",
        "original_callee_w0_return_semantics_proven":False,
        "callee_object_lifetime_or_CRI_async_proven":False,
    }
    if ins.mnemonic!="bl":
        return item
    direct=direct_branch(int.from_bytes(orig_word,"little"),at)
    if direct is None or direct[0]!="BL":
        raise ValueError("Missing ARM64 BL target at "+hex(at))
    target=direct[1]
    item["direct_target"]=hex(target)
    if target<0 or target+4>len(text) or target%4:
        item["target_outside_original_text"]=True
        return item
    item["target_outside_original_text"]=False
    end=min(target+MAX_CALLEE_WINDOW,len(text))
    decoded,graph=_decode_window(text,target,end)
    item["target_window_start"]=hex(target)
    item["target_window_end_exclusive"]=hex(end)
    item["target_window_sha256"]=hashlib.sha256(text[target:end]).hexdigest()
    item["target_first_words"]=[
        {"at":hex(pc),"word_le":text[pc:pc+4].hex(),
         "instruction":((decoded[pc].mnemonic+" "+decoded[pc].op_str).strip()
                        if pc in decoded else "UNDECODABLE")}
        for pc in range(target,min(target+TRANSCRIPT_BYTES,end),4)
    ]
    item["bounded_target_cfg"]=_callee_walk(graph,decoded,target,target,end)
    item["plt_import"]=_plt_import(text,mem,tags,target)
    item["window_not_function_boundary"]=True
    return item

def _w0_definitions_at_return(graph,decoded):
    tr=_trace(graph,decoded,start=TAIL_TARGET,lo=TAIL_TARGET,
              hi=TAIL_TARGET+TAIL_WINDOW_SIZE)
    if RET_SITE not in tr["returns"] or tr["escapes"]:
        raise ValueError("Original native tail RET or out-of-window flow changed")
    definitions=[]
    for origin in sorted(tr["returns"][RET_SITE]):
        if origin=="entry_w0_undefined_argument":
            definitions.append({"kind":"unknown_entry_W0","at":None,
                                "value":None})
        else:
            pc=int(origin.split("@",1)[1],16)
            info=tr["definitions"].get(pc)
            if info is None:
                raise ValueError("Lost original return-register W0 definition")
            definitions.append({**info,"word_le":None})
    return {
        "local_return_site":hex(RET_SITE),
        "machine_return_W0_reaching_definitions":definitions,
        "source_sites":[x["at"] for x in definitions if x["at"] is not None],
        "value_semantics_or_CRI_error_meaning_proven":False,
        "calls_may_modify_W0_and_memory":True,
    }

def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Exact original v1.70 Switch main SHA256 required")
    previous=inspect_tail(nso)
    observed=[int(x,16) for x in
              previous["tail_window_bounded_cfg"]["external_or_indirect_calls"]]
    if observed!=list(EXPECTED_SITES):
        raise ValueError("Exact eight native tail callsites changed")
    rows,mem=_read_image(nso)
    va,text,_=rows[0]
    if va!=0:
        raise ValueError("Expected NSO text base zero")
    tags=_tags(mem)
    graph,decoded=_decode_window(text,TAIL_TARGET,
                                  TAIL_TARGET+TAIL_WINDOW_SIZE)
    before=previous["tail_window_bounded_cfg"]
    if before["return_sites"]!=[hex(RET_SITE)] or before["other_exits"]:
        raise ValueError("Pinned tail static exit facts changed")
    calls=[_callee_report(text,mem,tags,pc) for pc in EXPECTED_SITES]
    source=_w0_definitions_at_return(graph,decoded)
    return {
        "status":"PINNED_FILEOPEN_EIGHT_NATIVE_TAIL_CALLEES_AND_W0_STATIC_ONLY",
        "source_main_sha256":digest,
        "original_tail":hex(TAIL_TARGET),
        "eight_original_callsite_addresses":[hex(x) for x in EXPECTED_SITES],
        "native_callsite_count":len(calls),
        "per_callsite_original_target_and_import_evidence":calls,
        "original_local_return_register_provenance":source,
        "calls_assumed_to_return_without_side_effect_model":True,
        "window_scope_not_entire_native_function_proven":True,
        "concrete_runtime_CRI_error_meaning_proven":False,
        "ownership_allocator_rollback_proven":False,
        "native_status_0x68_guard_0x1D8_lifecycle_proven":False,
        "callback_lock_unlock_async_completion_proven":False,
        "archive_priority_unbind_destructor_proven":False,
        "native_hook_abi_safe_proven":False,
        "native_patch_or_hook_added":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False,
        "gameplay_verified":False,
    }
