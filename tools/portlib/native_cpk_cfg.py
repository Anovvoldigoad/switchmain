"""Bounded ARM64 static CFG around pinned CPK/FileLoad candidate code.

Trace actual reachable basic instruction successors from relocated code-pointer
targets, never claim function bounds. Identifies conditional fallthrough, RET,
indirect BR/BLR, unconditional B, and BL return edge; branches outside window
remain unresolved. Main original SHA256 is pinned. This is NOT execution,
a proof of vtable ownership, or a safe hook/ABI authorization.
"""
import hashlib
import re
import struct
from collections import deque
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_cpk_indirect import RELA_TYPE, _image_and_relocations

# Suspected boundaries based on prior SHA-pinned source word+relocation facts.
# The bounds are ANALYSIS WINDOWS, NOT FUNCTION EXTENTS.
REGIONS={
    "candidate_106f394":(0x106F394,0x400),
    "relocated_106edb8":(0x106EDB8,0x180),
    "file_open_1170fb0":(0x1170FB0,0x300),
}
MAX_NODES=384
MAX_XREF_SAMPLES=24
BRANCHES={"b","bl","cbz","cbnz","tbz","tbnz"}
TERMINALS={"ret","retaa","retab","br","braa","brab"}


def _target(mnemonic,op_str):
    """Only A64 branch operands, never parse unrelated #imm as targets."""
    if mnemonic not in BRANCHES and not mnemonic.startswith("b."):
        return None
    matches=re.findall(r"#(-?0x[0-9a-fA-F]+|-?[0-9]+)",op_str)
    if not matches:
        return None
    return int(matches[-1],0)


def _edges(address,mnemonic,op_str):
    if mnemonic=="bl":
        return [("call",_target(mnemonic,op_str)),
                ("fallthrough_after_call",address+4)]
    if mnemonic=="b":
        return [("unconditional",_target(mnemonic,op_str))]
    if mnemonic in {"cbz","cbnz","tbz","tbnz"} or mnemonic.startswith("b."):
        return [("conditional",_target(mnemonic,op_str)),
                ("fallthrough",address+4)]
    if mnemonic=="blr":
        return [("indirect_call_unresolved",None),
                ("fallthrough_after_indirect_call",address+4)]
    if mnemonic in TERMINALS:
        return [("return_or_indirect_terminator",None)]
    return [("fallthrough",address+4)]


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Not the exact SHA-pinned v1.70 Switch main")
    rows,relocs=_image_and_relocations(nso)
    va,text,_=rows[0]
    if va!=0 or max(a+size for a,size in REGIONS.values())>len(text):
        raise ValueError("Original main text layout incompatible")
    code_relocs=[(slot,target) for slot,kind,target in relocs if kind==RELA_TYPE]
    for start in (0x106F394,0x106EDB8):
        if not any(target==start for _,target in code_relocs):
            raise ValueError("Relocation witness missing")
    boundaries={}
    for label,(start,size) in REGIONS.items():
        limit=start+size
        decoder=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
        word_map={}
        # Decode only one word at a time to prevent data-skipping and drift.
        for at in range(start,limit,4):
            data=text[at:at+4]
            rec=list(decoder.disasm(data,at))
            if len(rec)==1 and rec[0].size==4:
                word_map[at]=rec[0]
        seen=set(); queue=deque([start])
        events=[]; terminal=[];call_targets=[]
        reached_unparsed=[]
        while queue:
            at=queue.popleft()
            if at in seen:continue
            if at<start or at>=limit:
                continue
            if len(seen)>=MAX_NODES:
                raise ValueError("Static analysis node budget exceeded")
            seen.add(at)
            instr=word_map.get(at)
            if instr is None:
                reached_unparsed.append(f"0x{at:x}")
                continue
            edges=_edges(at,instr.mnemonic,instr.op_str)
            event={"offset":f"0x{at:x}","word_le":text[at:at+4].hex(),
                   "mnemonic":instr.mnemonic,"operands":instr.op_str,
                   "successors":[]}
            for kind,target in edges:
                edge={"kind":kind,"target":f"0x{target:x}" if target is not None else None}
                if target is not None:
                    edge["inside_analysis_window"]=start<=target<limit
                event["successors"].append(edge)
                if kind=="call" and target is not None:
                    call_targets.append({"site":f"0x{at:x}","callee":f"0x{target:x}"})
                if kind=="return_or_indirect_terminator":
                    terminal.append(f"0x{at:x}")
                if target is not None and kind!="call" and start<=target<limit:
                    queue.append(target)
            events.append(event)
        events.sort(key=lambda x:int(x["offset"],16))
        incoming=[]
        # Count actual direct B/BL instructions whose target == start.
        # Do not equate this with function ownership or callback invocation.
        for pc in range(0,len(text)-3,4):
            result=direct_branch(struct.unpack_from("<I",text,pc)[0],pc)
            if result is not None and result[1]==start:
                incoming.append({"site":f"0x{pc:x}","branch_kind":result[0]})
        reloc=[f"0x{slot:x}" for slot,target in code_relocs if target==start]
        boundaries[label]={
            "start_candidate":f"0x{start:x}",
            "analysis_window_size":size,
            "reachable_decoded_words":len(events),
            "reached_undecodable_words":reached_unparsed,
            "within_window_return_or_indirect_terminators":terminal,
            "direct_B_BL_incoming_count":len(incoming),
            "direct_B_BL_incoming_samples":incoming[:MAX_XREF_SAMPLES],
            "relative_relocation_incoming_slots":reloc[:MAX_XREF_SAMPLES],
            "relative_relocation_incoming_count":len(reloc),
            "direct_calls_found_in_reachable_code":call_targets,
            "decoded_reachable_instructions":events,
            "range_is_not_a_function_extent":True,
            "CALL_targets_not_walked":True,
            "possible_indirect_target_unresolved":True
        }
    # Assert prior corrected callsite is actually visited from *candidate*
    # entry's syntactically reachable CFG; if not, retain that as a bounded
    # negative fact, not grounds to infer the function start.
    target="0x106f404"
    reach={e["offset"] for e in boundaries["candidate_106f394"]["decoded_reachable_instructions"]}
    boundaries["candidate_106f394"]["legacy_callsite_syntactically_reachable"]=target in reach
    return {
        "status":"PINNED_STATIC_CONTROL_FLOW_CANDIDATES_ONLY",
        "main_sha256":digest,
        "source_relocation_records":len(relocs),
        "regions":boundaries,
        "bounded_cfg_not_a_discovered_abi":True,
        "function_boundaries_proven":False,
        "vtable_class_identity_proven":False,
        "CRI_async_completion_verified":False,
        "CRI_unbind_or_manager_destructor_verified":False,
        "archive_winner_verified":False,
        "Switch_parameter_loaders_wired":False,
        "native_hook_installed":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
