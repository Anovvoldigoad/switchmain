"""Bounded CFG evidence from CORRECTED native FileLoad prologue.

Unlike legacy 0x106F404 diagnostics, original v1.70 code begins with a
recorded frame prologue at 0x116F404. This tool verifies the eight-word
prologue, known BL callsites to FileOpen and status helper, and discovers
syntactically reachable paths, direct callers, return sites and unresolved
edges in a fixed analysis window. It does not prove actual CRI execution,
function extent, status semantics, native ABI or compatibility hooks.
"""
import hashlib
import struct
from collections import deque
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from .native_cpk_graph import MAIN_SHA256,direct_branch
from .native_fileload_corrected_entry import NEW_CANDIDATE,RECORDED_PROLOGUE
from .native_cpk_cfg import _edges
from .nso_profile import segments

ENTRY=NEW_CANDIDATE
END=0x116F750
CALLS={
 0x116F47C:("file_open",0x1170FB0),
 0x116F520:("status5_call_1",0x120661C),
 0x116F5C0:("status5_call_2",0x120661C),
}
MAX_REACHED=256


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Original exact Switch v1.70 main SHA256 required")
    va,code,_=segments(nso)[0]
    if va!=0 or END>len(code):
        raise ValueError("Pinned original text extent mismatch")
    if struct.unpack_from("<8I",code,ENTRY)!=RECORDED_PROLOGUE:
        raise ValueError("Source-proven corrected native FileLoad prologue mismatch")
    for site,(_,target) in CALLS.items():
        if direct_branch(struct.unpack_from("<I",code,site)[0],site)!=("BL",target):
            raise ValueError("Expected pinned FileLoad direct call missing: "+hex(site))
    decoder=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    decoded={}
    for at in range(ENTRY,END,4):
        raw=code[at:at+4]
        inst=list(decoder.disasm(raw,at))
        if len(inst)==1 and inst[0].size==4:
            decoded[at]=inst[0]
    queue=deque([ENTRY])
    observed=set();edges=[];events=[];terms=[];outside=[];indirects=[]
    while queue:
        pc=queue.popleft()
        if pc in observed or not ENTRY<=pc<END:continue
        if len(observed)>=MAX_REACHED:
            raise ValueError("FileLoad CFG reached bounded node limit")
        observed.add(pc)
        inst=decoded.get(pc)
        if inst is None:
            events.append({"site":hex(pc),"kind":"undecodable"})
            continue
        succ=_edges(pc,inst.mnemonic,inst.op_str)
        record={"offset":f"0x{pc:x}","word_le":code[pc:pc+4].hex(),
                "mnemonic":inst.mnemonic,"operands":inst.op_str,
                "successors":[]}
        for kind,target in succ:
            entry={"kind":kind,"target":f"0x{target:x}" if target is not None else None}
            record["successors"].append(entry)
            if kind=="return_or_indirect_terminator":
                terms.append(hex(pc))
            if kind=="indirect_call_unresolved":
                indirects.append(hex(pc))
            if target is not None and kind!="call":
                if ENTRY<=target<END:queue.append(target)
                else:outside.append({"from":hex(pc),"kind":kind,"to":hex(target)})
        events.append(record)
    events.sort(key=lambda x:int(x.get("offset",x.get("site")),16))
    # Compare syntactic CFG reachability without asserting every call executes.
    named=[]
    for site,(name,target) in CALLS.items():
        named.append({
            "name":name,
            "callsite":f"0x{site:x}","target":f"0x{target:x}",
            "actual_machine_word_BL_target_verified":True,
            "syntactically_reachable_from_corrected_prologue":site in observed,
            "executed_in_game_proven":False
        })
    incoming=[]
    for pc in range(0,len(code)-3,4):
        edge=direct_branch(struct.unpack_from("<I",code,pc)[0],pc)
        if edge and edge[1]==ENTRY:
            incoming.append({"caller":f"0x{pc:x}","kind":edge[0]})
    # Check named source-related candidate caller independently.
    source_caller=direct_branch(struct.unpack_from("<I",code,0x116F29C)[0],0x116F29C)
    return {
        "status":"CORRECTED_NATIVE_FILELOAD_BOUNDED_CONTROL_FLOW_ONLY",
        "pinned_main_sha256":digest,
        "original_entry_candidate":"0x116f404",
        "old_mislocated_anchor":"0x106f404",
        "original_8_word_prologue_matches":True,
        "window_end_exclusive":f"0x{END:x}",
        "window_is_not_a_proven_function_extent":True,
        "reachable_decoded_instruction_count":sum("offset" in x for x in events),
        "return_or_indirect_terminators":terms,
        "indirect_calls_without_resolved_targets":indirects,
        "out_of_window_control_flow_edges":outside[:64],
        "out_of_window_edges_truncated":len(outside)>64,
        "observed_direct_incoming_branch_count":len(incoming),
        "observed_direct_incoming_branches":incoming[:32],
        "source_comment_caller_at_0x116f29c":{
            "kind":source_caller[0] if source_caller else None,
            "target":f"0x{source_caller[1]:x}" if source_caller else None,
            "is_direct_BL_to_corrected_entry":source_caller==("BL",ENTRY)
        },
        "named_callsite_witnesses":named,
        "reachable_instructions":events,
        "native_status_field_semantics_verified":False,
        "file_open_result_to_status5_causation_proven":False,
        "async_completion_verified":False,
        "unbind_or_destructor_verified":False,
        "archive_lookup_priority_verified":False,
        "runtime_AAPCS64_function_signature_verified":False,
        "native_hook_added":False,"gameplay_verified":False,"full_moddingapi":False
    }
