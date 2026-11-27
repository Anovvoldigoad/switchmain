"""Pinned FileLoad error callsites -> status setter candidate machine evidence.

Native 0x116F404 (corrected prologue from previous CI) contains two
word-exact MOV W1,#5 / MOV X0,X20 / BL 0x120661C call sequences.
Second sequence is guarded by LDR W8,[X22,#0x1D8], CMP W8,#1 and B.NE.
This tool additionally transcribes the *actual target implementation*
and the opening failure branch near the observed 0x1170FB0 FileOpen BL.

A status-like setter call does not prove CPK async completion, object
lifetime, successful archive priority, ABI for a new trampoline, or
eventual gameplay. No hooks or native storage bytes are changed.
"""
import hashlib
import struct
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM,CS_GRP_CALL,CS_GRP_JUMP,CS_GRP_RET
from capstone.arm64_const import ARM64_OP_IMM,ARM64_OP_MEM
from .native_cpk_graph import MAIN_SHA256,direct_branch
from .nso_profile import segments

STATUS_HELPER=0x120661C
HELPER_WINDOW=(0x120661C,0x12066BC)
OPEN_CORRIDOR=(0x116F460,0x116F4B0)
STATUS_CALL_WITNESSES={
 0x116F518:("mov","w1, #5"),
 0x116F51C:("mov","x0, x20"),
 0x116F520:("bl","#0x120661c"),
 0x116F5AC:("ldr","w8, [x22, #0x1d8]"),
 0x116F5B0:("cmp","w8, #1"),
 0x116F5B4:("b.ne","#0x116f5c4"),
 0x116F5B8:("mov","w1, #5"),
 0x116F5BC:("mov","x0, x20"),
 0x116F5C0:("bl","#0x120661c"),
}
FILE_OPEN_EDGE=(0x116F47C,0x1170FB0)
SERVICE_WINDOW=(0x1215358,0x12153D8)
SERVICE_ENTRYPOINTS=(0x1215358,0x1215374)
SERVICE_TARGET_WINDOW=(0x1158C90,0x1158D90)
SERVICE_TARGETS=(0x1158C90,0x1158D10,0x1158D30)
SERVICE_REQUIRED_TARGET_EDGES=(
 (0x1215364,"B",0x1158C90),
 (0x1215380,"B",0x1158D10),
 (0x12153A8,"BL",0x1158D30),
)

# Direct dependencies observed in the bounded dispatch-target traces. These
# are code addresses, not proven function starts or named OS primitives.
SERVICE_DEPENDENCY_TARGETS=(0x12A35B4,0x12A35BC,0x12F4CF0,0x12F50E0)
SERVICE_DEPENDENCY_WINDOWS=(
 (0x12A35B4,0x12A36B4,(0x12A35B4,0x12A35BC)),
 (0x12F4CF0,0x12F4DF0,(0x12F4CF0,)),
 (0x12F50E0,0x12F51E0,(0x12F50E0,)),
)
SERVICE_DISPATCH_X0_ADJUSTMENT=8
SERVICE_WRAPPER_OWNER_OFFSET=8
SERVICE_WRAPPER_COUNT_OFFSET=12


def _words(code,start,end):
    cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    result=[]
    for at in range(start,end,4):
        word=code[at:at+4]
        seq=list(cs.disasm(word,at))
        result.append({
            "at":f"0x{at:x}",
            "word_le":word.hex(),
            "mnemonic":seq[0].mnemonic if len(seq)==1 and seq[0].size==4 else "UNPARSED_A64",
            "operands":seq[0].op_str if len(seq)==1 and seq[0].size==4 else ""
        })
    return result


def _service_words(text,start,end):
    if start<0 or end>len(text) or end<=start or (start&3) or (end&3):
        raise ValueError("Invalid aligned service-code window")
    cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    cs.detail=True
    result=[]
    for at in range(start,end,4):
        raw=text[at:at+4]
        decoded=list(cs.disasm(raw,at))
        if len(decoded)!=1 or decoded[0].size!=4:
            result.append({
                "at":f"0x{at:x}","word_le":raw.hex(),
                "mnemonic":"UNPARSED_A64","operands":"",
                "direct_branch_kind":None,"direct_branch_target":None,
                "read_registers":[],"written_registers":[],
                "memory_operands":[]
            })
            continue
        ins=decoded[0]
        branch=direct_branch(struct.unpack_from("<I",raw)[0],at)
        try:
            reads,writes=ins.regs_access()
        except Exception as exc:
            raise ValueError("AArch64 register access decode failed at "+hex(at)) from exc
        memory=[]
        for op in ins.operands:
            if op.type!=ARM64_OP_MEM:
                continue
            memory.append({
                "base_register":ins.reg_name(op.mem.base) if op.mem.base else None,
                "index_register":ins.reg_name(op.mem.index) if op.mem.index else None,
                "displacement":op.mem.disp,
                "writeback":bool(getattr(ins,"writeback",False)),
                "direction":("write" if ins.mnemonic.startswith("st") else
                             "read" if ins.mnemonic.startswith("ld") else "unknown")
            })
        result.append({
            "at":f"0x{at:x}","word_le":raw.hex(),
            "mnemonic":ins.mnemonic,"operands":ins.op_str,
            "direct_branch_kind":branch[0] if branch else None,
            "direct_branch_target":hex(branch[1]) if branch else None,
            "read_registers":sorted({ins.reg_name(x) for x in reads}),
            "written_registers":sorted({ins.reg_name(x) for x in writes}),
            "memory_operands":memory
        })
    return result


def _service_window(text):
    start,end=SERVICE_WINDOW
    instructions=_service_words(text,start,end)
    by_at={int(row["at"],16):row for row in instructions}
    entrypoints=[]
    for at in SERVICE_ENTRYPOINTS:
        row=by_at.get(at)
        if row is None:
            raise ValueError("Required service target is outside the bounded window")
        entrypoints.append({
            "at":hex(at),"word_le":row["word_le"],
            "mnemonic":row["mnemonic"],"operands":row["operands"]
        })
    return {
        "start":hex(start),"end_exclusive":hex(end),
        "window_bytes":end-start,
        "window_sha256":hashlib.sha256(text[start:end]).hexdigest(),
        "entrypoints":entrypoints,
        "instructions":instructions,
        "bounded_window_not_function_extent":True,
        "lock_unlock_semantics_verified":False,
        "service_function_boundaries_verified":False
    }


def _bounded_trace(text,start,end,entry,max_instructions=256):
    """Trace direct control flow only inside a fixed byte window; never infer function extent."""
    if (start<0 or end>len(text) or end<=start or (start&3) or (end&3)
            or entry<start or entry>=end or (entry&3) or max_instructions<1):
        raise ValueError("Invalid bounded target trace")
    cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    cs.detail=True
    pending=[entry]
    visited=set()
    returns=[]
    direct_calls=[]
    indirect_calls=[]
    direct_branches=[]
    indirect_branches=[]
    out_of_window=[]
    decode_failures=[]
    budget_exhausted=False

    def enqueue(from_pc,target,kind):
        if start<=target<end:
            pending.append(target)
        else:
            out_of_window.append({
                "from":hex(from_pc),"target":hex(target),"kind":kind
            })

    while pending:
        pc=pending.pop()
        if pc in visited:
            continue
        if len(visited)>=max_instructions:
            budget_exhausted=True
            break
        raw=text[pc:pc+4]
        decoded=list(cs.disasm(raw,pc))
        if len(decoded)!=1 or decoded[0].size!=4:
            decode_failures.append(hex(pc))
            continue
        ins=decoded[0]
        visited.add(pc)
        mnemonic=ins.mnemonic.lower()
        target=next((int(op.imm) for op in ins.operands
                     if op.type==ARM64_OP_IMM),None)

        if mnemonic in ("ret","eret","drps") or ins.group(CS_GRP_RET):
            returns.append(hex(pc))
            continue
        if (mnemonic in ("bl","blr","blraa","blrab","blraaz","blrabz")
                or ins.group(CS_GRP_CALL)):
            if target is None:
                indirect_calls.append({
                    "at":hex(pc),"mnemonic":mnemonic,"operands":ins.op_str
                })
            else:
                direct_calls.append({
                    "at":hex(pc),"target":hex(target),"kind":"BL"
                })
            enqueue(pc,pc+4,"fallthrough")
            continue
        if mnemonic=="b":
            if target is None:
                indirect_branches.append({
                    "at":hex(pc),"mnemonic":mnemonic,"operands":ins.op_str
                })
            else:
                direct_branches.append({
                    "at":hex(pc),"target":hex(target),"kind":"B"
                })
                enqueue(pc,target,"B")
            continue
        if mnemonic.startswith("b.") or mnemonic in ("cbz","cbnz","tbz","tbnz"):
            if target is None:
                indirect_branches.append({
                    "at":hex(pc),"mnemonic":mnemonic,"operands":ins.op_str
                })
            else:
                direct_branches.append({
                    "at":hex(pc),"target":hex(target),"kind":mnemonic
                })
                enqueue(pc,target,mnemonic)
            enqueue(pc,pc+4,"fallthrough")
            continue
        if (mnemonic in ("br","braa","brab","braaz","brabz")
                or ins.group(CS_GRP_JUMP)):
            indirect_branches.append({
                "at":hex(pc),"mnemonic":mnemonic,"operands":ins.op_str
            })
            continue
        enqueue(pc,pc+4,"fallthrough")

    return {
        "entry":hex(entry),
        "window_start":hex(start),
        "window_end_exclusive":hex(end),
        "reachable_addresses":[hex(x) for x in sorted(visited)],
        "reachable_instruction_count":len(visited),
        "direct_calls":direct_calls,
        "indirect_calls":indirect_calls,
        "direct_branches":direct_branches,
        "indirect_branches":indirect_branches,
        "returns":returns,
        "out_of_window_edges":out_of_window,
        "decode_failures":decode_failures,
        "budget_exhausted":budget_exhausted,
        "control_flow_is_bounded":True,
        "function_boundary_proven":False
    }


def _service_target_window(text):
    start,end=SERVICE_TARGET_WINDOW
    instructions=_service_words(text,start,end)
    by_at={int(row["at"],16):row for row in instructions}
    entrypoints=[]
    for at in SERVICE_TARGETS:
        row=by_at.get(at)
        if row is None:
            raise ValueError("Required service dispatch target is outside bounded window")
        entrypoints.append({
            "at":hex(at),"word_le":row["word_le"],
            "mnemonic":row["mnemonic"],"operands":row["operands"]
        })
    traces=[_bounded_trace(text,start,end,at) for at in SERVICE_TARGETS]
    return {
        "start":hex(start),"end_exclusive":hex(end),
        "window_bytes":end-start,
        "window_sha256":hashlib.sha256(text[start:end]).hexdigest(),
        "entrypoints":entrypoints,
        "instructions":instructions,
        "bounded_window_not_function_extent":True,
        "bounded_traces":traces,
        "lock_unlock_semantics_verified":False,
        "ownership_lifecycle_verified":False,
        "async_completion_verified":False
    }


def _service_dependency_window(text,start,end,entries):
    instructions=_service_words(text,start,end)
    by_at={int(row["at"],16):row for row in instructions}
    if not entries or len(set(entries))!=len(entries):
        raise ValueError("Invalid service dependency entry list")
    entrypoints=[]
    for at in entries:
        row=by_at.get(at)
        if row is None:
            raise ValueError("Service dependency entry outside bounded window")
        entrypoints.append({
            "at":hex(at),"word_le":row["word_le"],
            "mnemonic":row["mnemonic"],"operands":row["operands"]
        })
    traces=[_bounded_trace(text,start,end,at) for at in entries]
    return {
        "start":hex(start),"end_exclusive":hex(end),
        "window_bytes":end-start,
        "window_sha256":hashlib.sha256(text[start:end]).hexdigest(),
        "entrypoints":entrypoints,"instructions":instructions,
        "bounded_window_not_function_extent":True,
        "bounded_traces":traces,
        "function_boundaries_verified":False,
        "dependency_semantics_verified":False
    }


def _service_dependency_windows(text):
    return [_service_dependency_window(text,start,end,entries)
            for start,end,entries in SERVICE_DEPENDENCY_WINDOWS]


def _service_target_inbound_edges(text,targets=SERVICE_TARGETS):
    targets=tuple(targets)
    incoming={target:[] for target in targets}
    for pc in range(0,len(text)-3,4):
        word=struct.unpack_from("<I",text,pc)[0]
        branch=direct_branch(word,pc)
        if branch and branch[1] in incoming:
            incoming[branch[1]].append({
                "caller":hex(pc),"kind":branch[0],
                "word_le":text[pc:pc+4].hex()
            })
    return {hex(target):incoming[target] for target in targets}


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Exact pinned v1.70 original main required")
    rows=segments(nso)
    va,text,_=rows[0]
    if va!=0 or max(HELPER_WINDOW[1],OPEN_CORRIDOR[1],SERVICE_WINDOW[1],
                    SERVICE_TARGET_WINDOW[1],
                    *(end for _,end,_ in SERVICE_DEPENDENCY_WINDOWS))>len(text):
        raise ValueError("Pinned original main geometry mismatch")
    witnesses=[]
    for at,(mnemonic,operands) in STATUS_CALL_WITNESSES.items():
        w=_words(text,at,at+4)[0]
        if (w["mnemonic"],w["operands"])!=(mnemonic,operands):
            raise ValueError("Original FileLoad failure word differs at "+hex(at))
        witnesses.append(w)
    for callsite in (0x116F520,0x116F5C0):
        if direct_branch(struct.unpack_from("<I",text,callsite)[0],callsite)!=(
                "BL",STATUS_HELPER):
            raise ValueError("Native status candidate helper call edge absent")
    file_open=direct_branch(struct.unpack_from("<I",text,FILE_OPEN_EDGE[0])[0],FILE_OPEN_EDGE[0])
    if file_open!=("BL",FILE_OPEN_EDGE[1]):
        raise ValueError("Native file-open callsite altered")
    helper=_words(text,*HELPER_WINDOW)
    opening=_words(text,*OPEN_CORRIDOR)
    service=_service_window(text)
    service_targets=_service_target_window(text)
    dependency_windows=_service_dependency_windows(text)
    all_targets=SERVICE_TARGETS+SERVICE_DEPENDENCY_TARGETS
    all_edges=_service_target_inbound_edges(text,all_targets)
    target_edges={hex(target):all_edges[hex(target)] for target in SERVICE_TARGETS}
    dependency_edges={hex(target):all_edges[hex(target)]
                      for target in SERVICE_DEPENDENCY_TARGETS}
    for caller,kind,target in SERVICE_REQUIRED_TARGET_EDGES:
        if not any(row["caller"]==hex(caller) and row["kind"]==kind
                   for row in target_edges[hex(target)]):
            raise ValueError("Required FileLoad service target edge absent at "+hex(caller))
    required_dependency_edges=(
        (0x1158CBC,"BL",0x12A35B4),
        (0x1158D2C,"B",0x12A35BC),
        (0x1158C9C,"BL",0x12F4CF0),
        (0x1158CA4,"BL",0x12F50E0),
    )
    for caller,kind,target in required_dependency_edges:
        if not any(row["caller"]==hex(caller) and row["kind"]==kind
                   for row in dependency_edges[hex(target)]):
            raise ValueError("Required FileLoad service dependency edge absent at "+hex(caller))
    return {
        "status":"PINNED_NATIVE_FILELOAD_STATUS_CALLSITE_WITNESSES_ONLY",
        "main_sha256":digest,
        "corrected_native_fileload_entry_prologue":"0x116f404",
        "known_file_open_bl":{"at":"0x116f47c","callee":"0x1170fb0"},
        "status_code_argument_value":5,
        "status_setter_candidate_target":"0x120661c",
        "verified_status_argument_and_callsite_words":witnesses,
        "second_sequence_read_error_field_offset":0x1d8,
        "second_sequence_compares_error_field_to":1,
        "helper_code":{
            "start":"0x120661c","window_bytes":HELPER_WINDOW[1]-HELPER_WINDOW[0],
            "window_sha256":hashlib.sha256(text[slice(*HELPER_WINDOW)]).hexdigest(),
            "instructions":helper
        },
        "file_open_return_handling_near_call":{
            "start":"0x116f460",
            "window_sha256":hashlib.sha256(text[slice(*OPEN_CORRIDOR)]).hexdigest(),
            "instructions":opening
        },
        "service_code_window":service,
        "service_target_code_window":service_targets,
        "service_target_incoming_direct_edges":target_edges,
        "service_dependency_code_windows":dependency_windows,
        "service_dependency_incoming_direct_edges":dependency_edges,
        "service_dependency_targets_are_function_boundaries":False,
        "service_dependency_thread_token_semantics_verified":False,
        "service_dependency_mutex_primitive_semantics_verified":False,
        "service_dependency_lifecycle_semantics_verified":False,
        "service_dispatch_x0_adjustment":SERVICE_DISPATCH_X0_ADJUSTMENT,
        "service_wrapper_owner_field_offset":SERVICE_WRAPPER_OWNER_OFFSET,
        "service_wrapper_count_field_offset":SERVICE_WRAPPER_COUNT_OFFSET,
        "service_target_lock_unlock_implementation_verified":False,
        "service_target_function_boundaries_verified":False,
        "service_target_ownership_lifecycle_verified":False,
        "service_target_async_completion_verified":False,
        "service_semantics_verified":False,
        "mutex_lock_unlock_implementation_verified":False,
        "service_function_boundaries_verified":False,
        "service_runtime_binding_verified":False,
        "status_helper_object_field_write_verified":False,
        "file_open_failed_path_to_status_helper_verified":False,
        "native_status_field_semantics_not_verified":True,
        "ABI_safe_new_hook_proven":False,
        "CPK_async_completion_verified":False,
        "CPK_archive_precedence_verified":False,
        "CPK_unbind_destructor_verified":False,
        "new_hook_installed":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
