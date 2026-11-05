"""Exact-main original FileOpen tail: bounded register argument and indirect BR dataflow.

Adds structural evidence for candidate AAPCS64 arguments at each of eight BLs
and for the register feeding any reachable BR terminators in each callee.
Everything is path-insensitive, bounded, with external effects unknown.
Do not turn a source register into an object layout/ownership/CRI ABI claim.
"""
import hashlib
from collections import deque

from .native_cpk_graph import MAIN_SHA256
from .native_fileopen_tail import TAIL_TARGET,TAIL_WINDOW_SIZE
from .native_fileopen_tail_callees import (
    EXPECTED_SITES,inspect as inspect_callees,MAX_CALLEE_WINDOW)
from .native_fileopen_callees import (
    _decode_window,_predecessors,_writer_origins)
from .nso_profile import segments

MAX_GRAPH_WORDS=96
ARGUMENTS=("x0","x1","x2","x3")
RET_CALL_GPRS=("x0",)
TARGET_TRACE_WORDS=16

def _reached(graph,entry,start,end):
    queue=deque([entry])
    seen=set()
    escapes=[]
    while queue:
        pc=queue.popleft()
        if pc in seen:
            continue
        if len(seen)>=MAX_GRAPH_WORDS:
            raise ValueError("Original bounded callsite provenance budget exhausted")
        seen.add(pc)
        if pc not in graph or not start<=pc<end:
            escapes.append(hex(pc))
            continue
        for kind,target in graph[pc]:
            if kind=="call":
                continue
            if target is not None and target not in seen:
                queue.append(target)
    return seen,sorted(set(escapes))

def _arg_origins(graph,decoded,reachable,site,entry):
    predecessors=_predecessors(graph,reachable,entry,max(reachable)+4)
    args={}
    for reg in ARGUMENTS:
        row=_writer_origins(predecessors,decoded,site,reg,entry=entry)
        args[reg]=row
    return args

def _indirect_branch_feeds(graph,decoded,reachable,entry):
    pred=_predecessors(graph,reachable,entry,max(reachable)+4)
    rows=[]
    for pc in sorted(reachable):
        ins=decoded.get(pc)
        if ins is None or ins.mnemonic not in ("br","braa","brab"):
            continue
        reg=ins.op_str.split(",",1)[0].strip().lower()
        if not reg.startswith("x") or not reg[1:].isdigit():
            rows.append({"at":hex(pc),"register_unresolved":ins.op_str})
            continue
        rows.append({"at":hex(pc),"instruction":ins.mnemonic+" "+ins.op_str,
                     "branch_register":reg,
                     "possible_original_register_writers":
                         _writer_origins(pred,decoded,pc,reg,entry=entry),
                     "runtime_branch_target_proven":False})
    return rows

def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Expected exact original Switch v1.70 main SHA256")
    baseline=inspect_callees(nso)
    va,text,_=segments(nso)[0]
    if va:
        raise ValueError("Unexpected original executable base")
    tail_stop=TAIL_TARGET+TAIL_WINDOW_SIZE
    decoded,graph=_decode_window(text,TAIL_TARGET,tail_stop)
    reachable,escapes=_reached(graph,TAIL_TARGET,TAIL_TARGET,tail_stop)
    if escapes or len(reachable)!=53:
        raise ValueError("Original FileOpen bounded native tail geometry changed")
    rows=[]
    for source in baseline["per_callsite_original_target_and_import_evidence"]:
        site=int(source["site"],16)
        if site not in reachable or site not in EXPECTED_SITES:
            raise ValueError("Original tail callsite not reached")
        direct=source["direct_target"]
        result={"site":source["site"],"word_le":source["word_le"],
                "original_instruction":source["instruction"],
                "source_tail_implicit_argument_register_writers":
                    _arg_origins(graph,decoded,reachable,site,TAIL_TARGET),
                "native_call_execution_proven":False,
                "actual_original_ABI_proven":False,
                "callee_target":direct}
        if direct is not None and not source.get("target_outside_original_text",False):
            start=int(direct,16)
            stop=min(start+MAX_CALLEE_WINDOW,len(text))
            target_decoded,target_graph=_decode_window(text,start,stop)
            target_reached,target_escapes=_reached(target_graph,start,start,stop)
            result["bounded_target_reachable"]=len(target_reached)
            result["bounded_target_external_edges"]=target_escapes
            result["native_indirect_br_register_sources"]=_indirect_branch_feeds(
                target_graph,target_decoded,target_reached,start)
            result["original_machine_word_sample"]=[
                {"at":hex(pc),"word_le":text[pc:pc+4].hex(),
                 "instruction":((target_decoded[pc].mnemonic+" "+target_decoded[pc].op_str).strip()
                       if pc in target_decoded else "UNDECODABLE")}
                for pc in range(start,min(start+TARGET_TRACE_WORDS*4,stop),4)]
        rows.append(result)
    if [int(r["site"],16) for r in rows]!=list(EXPECTED_SITES):
        raise ValueError("Original callsite identity/order changed")
    return {
        "status":"EXACT_ORIGINAL_FILEOPEN_TAIL_CALL_ARGUMENTS_AND_BR_WRITER_CANDIDATES",
        "source_main_sha256":digest,
        "original_tail_entry":hex(TAIL_TARGET),
        "tail_bounded_reached_instructions":len(reachable),
        "callsite_provenance":rows,
        "local_return_W0_reaching_definitions":
            baseline["original_local_return_register_provenance"],
        "candidate_argument_registers_are_not_proven_ABI":True,
        "indirect_branch_register_writers_are_not_proven_target_values":True,
        "native_CRI_failure_state_proven":False,
        "native_object_allocation_and_lifetime_proven":False,
        "callback_lock_async_unbind_destructor_proven":False,
        "archive_precedence_proven":False,
        "new_hook_or_binary_patch_installed":False,
        "safe_hook_abi_proven":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False,
        "gameplay_verified":False,
    }
