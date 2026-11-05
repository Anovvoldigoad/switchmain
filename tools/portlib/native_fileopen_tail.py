"""Original native FileOpen BL -> X0+0x18 B-tail callsite evidence.

Disassemble verified wrapper 0x115FC2C and its immediate B target
0x115EBD8. Trace bounded machine-code return/call/field candidates at the
target without asserting complete boundaries, runtime execution, ABI safety,
real CRI outcomes, or destructor/async ownership.
"""
import hashlib
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from .native_cpk_graph import MAIN_SHA256,direct_branch
from .native_fileopen_returns import ENTRY,END,_build_graph,_trace
from .native_fileopen_callees import _decode_window,_callee_walk,_predecessors,_writer_origins
from .native_fileopen_import import inspect as inspect_import
from .nso_profile import segments

FILEOPEN_CALL=0x117103C
WRAPPER=0x115FC2C
TAIL_SITE=0x115FC30
TAIL_TARGET=0x115EBD8
RESULT_CMP=0x1171040
RESULT_BRANCH=0x1171048
TAIL_WINDOW_SIZE=0x200

def _decode(text,at):
    cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    cs.detail=True
    one=list(cs.disasm(text[at:at+4],at))
    if len(one)!=1 or one[0].size!=4:
        raise ValueError("Undecodable pinned original AArch64 word")
    return one[0]

def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Exact original Switch 1.70 main only")
    got=inspect_import(nso)
    if not any(r["type_name"]=="R_AARCH64_JUMP_SLOT" and
               r["original_dynamic_symbol"].get("name")=="strncpy"
               for r in got["original_dynamic_relocations_to_slot"]):
        raise ValueError("Expected original PLT slot imported strncpy not found")
    va,text,_=segments(nso)[0]
    if va or TAIL_TARGET+TAIL_WINDOW_SIZE>len(text):
        raise ValueError("Original native tail function bounds invalid")
    checks=((FILEOPEN_CALL,"BL",WRAPPER),(TAIL_SITE,"B",TAIL_TARGET))
    for site,kind,target in checks:
        actual=direct_branch(int.from_bytes(text[site:site+4],"little"),site)
        if actual!=(kind,target):
            raise ValueError("Original native direct branch fingerprint differs")
    wrapper=_decode(text,WRAPPER)
    cmp=_decode(text,RESULT_CMP)
    branch=_decode(text,RESULT_BRANCH)
    if (wrapper.mnemonic,wrapper.op_str)!=("add","x0, x0, #0x18"):
        raise ValueError("Original wrapper X0 offset was modified")
    if (cmp.mnemonic,cmp.op_str)!=("cmp","w0, #1") or (
        branch.mnemonic,branch.op_str)!=("b.lt","#0x117106c"):
        raise ValueError("FileOpen native wrapper return condition differs")
    graph,decoded=_build_graph(text)
    tr=_trace(graph,decoded)
    pred=_predecessors(graph,tr["reachable"],ENTRY,END)
    x0=_writer_origins(pred,decoded,FILEOPEN_CALL,"x0")
    subgraph,edges=_decode_window(text,TAIL_TARGET,TAIL_TARGET+TAIL_WINDOW_SIZE)
    bounded=_callee_walk(edges,subgraph,TAIL_TARGET,TAIL_TARGET,
                         TAIL_TARGET+TAIL_WINDOW_SIZE)
    sample=[]
    for at in range(TAIL_TARGET,TAIL_TARGET+0x80,4):
        ins=subgraph.get(at)
        sample.append({
            "at":hex(at),"word_le":text[at:at+4].hex(),
            "instruction":(ins.mnemonic+" "+ins.op_str).strip()
                            if ins is not None else "UNDECODED"
        })
    return {
        "status":"PINNED_FILEOPEN_X0_PLUS_0X18_TAIL_TO_NATIVE_TARGET_STATIC_ONLY",
        "original_main_sha256":digest,
        "original_imported_helper":"strncpy",
        "original_fileopen_callsite":hex(FILEOPEN_CALL),
        "original_wrapper":hex(WRAPPER),
        "original_wrapper_first_word_le":text[WRAPPER:WRAPPER+4].hex(),
        "original_wrapper_first_instruction":"ADD X0,X0,#0x18",
        "original_wrapper_tail_B_site":hex(TAIL_SITE),
        "original_native_tail_target":hex(TAIL_TARGET),
        "original_tail_B_word_le":text[TAIL_SITE:TAIL_SITE+4].hex(),
        "native_fileopen_X0_inbound_source_candidates":x0,
        "original_fileopen_result_cmp":{
            "at":hex(RESULT_CMP),"word_le":text[RESULT_CMP:RESULT_CMP+4].hex(),
            "instruction":cmp.mnemonic+" "+cmp.op_str,
            "following_original_branch":{
                "at":hex(RESULT_BRANCH),
                "word_le":text[RESULT_BRANCH:RESULT_BRANCH+4].hex(),
                "instruction":branch.mnemonic+" "+branch.op_str,
                "branch_taken_to_W0_zero_literal":True,
                "runtime_branch_taken_proven":False}},
        "tail_window_start":hex(TAIL_TARGET),
        "tail_window_end_exclusive":hex(TAIL_TARGET+TAIL_WINDOW_SIZE),
        "tail_window_sha256":hashlib.sha256(text[TAIL_TARGET:TAIL_TARGET+TAIL_WINDOW_SIZE]).hexdigest(),
        "tail_window_original_first_words":sample,
        "tail_window_bounded_cfg":bounded,
        "tail_window_may_cross_native_function_boundaries":True,
        "x0_pointer_plus_0x18_type_and_ownership_proven":False,
        "tail_native_W0_semantics_proven":False,
        "original_CRI_error_or_archive_failure_executed":False,
        "real_callbacks_locks_async_unbind_destructor_proven":False,
        "native_hook_ABI_safe_proven":False,
        "new_native_hook_installed":False,
        "gameplay_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False
    }
