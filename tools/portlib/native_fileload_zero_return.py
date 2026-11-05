"""Original SHA-pinned FileOpen zero-return branch to native status5 candidate.

No callback, CPK status service or game-memory implementation is invented.
Proof is bounded and syntactic: W0==0 immediately after FileOpen BL takes
the original CBZ. Then enumerate static control-flow paths to original
status setter BL, treating other calls as returning normally. This does
NOT establish real CRI error causes, callback timing or live ABI.
"""
import hashlib
from collections import deque
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from .native_cpk_graph import MAIN_SHA256,direct_branch
from .native_fileload_corridor_cfg import ENTRY,END
from .native_cpk_cfg import _edges
from .nso_profile import segments

FILEOPEN_BL=0x116F47C
ZERO_BRANCH=0x116F480
ZERO_TARGET=0x116F4D8
STATUS1=0x116F520
STATUS2=0x116F5C0
SETTER=0x120661C
MAX_VISITS=300


def _one(code,at):
    dis=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    ins=list(dis.disasm(code[at:at+4],at))
    if len(ins)!=1 or ins[0].size!=4:
        raise ValueError("Failed to decode pinned original AArch64 word "+hex(at))
    return ins[0]


def _path(code,start,target):
    queue=deque([(start,[start])]);seen=set()
    while queue:
        at,path=queue.popleft()
        if at in seen:continue
        seen.add(at)
        if len(seen)>MAX_VISITS:
            raise ValueError("Branch proof bound exceeded")
        if at==target:return path
        if not ENTRY<=at<END:continue
        ins=_one(code,at)
        for kind,nxt in _edges(at,ins.mnemonic,ins.op_str):
            # Follow branch/fallthrough only; do not treat call entry
            # into a separate function as an intra-function edge.
            if nxt is not None and kind!="call" and nxt not in seen and ENTRY<=nxt<END:
                queue.append((nxt,path+[nxt]))
    return None


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Exact original Switch 1.70 main SHA256 mandatory")
    va,code,_=segments(nso)[0]
    if va!=0 or END>len(code):
        raise ValueError("Original main executable geometry mismatch")
    if direct_branch(int.from_bytes(code[FILEOPEN_BL:FILEOPEN_BL+4],"little"),FILEOPEN_BL)!=("BL",0x1170FB0):
        raise ValueError("Original file-open BL byte witness changed")
    zero=_one(code,ZERO_BRANCH)
    if (zero.mnemonic,zero.op_str)!=("cbz",f"w0, #0x{ZERO_TARGET:x}"):
        raise ValueError("FileOpen W0==0 branch word witness changed")
    first=_path(code,ZERO_TARGET,STATUS1)
    second=_path(code,ZERO_TARGET,STATUS2)
    before_first=_one(code,STATUS1)
    before_second=_one(code,STATUS2)
    if (before_first.mnemonic,before_second.mnemonic)!=("bl","bl"):
        raise ValueError("Status5 callsites are no longer two original BL")
    for at in (STATUS1,STATUS2):
        if direct_branch(int.from_bytes(code[at:at+4],"little"),at)!=("BL",SETTER):
            raise ValueError("Native status call callee mismatch")
    check=_one(code,0x116F5B4)
    if (check.mnemonic,check.op_str)!=("b.ne"," #0x116f5c4".strip()):
        raise ValueError("Second status setter 0x1D8 compare branch changed")
    witness={
        "source_callsite":"0x116f47c",
        "source_target":"0x1170fb0",
        "following_branch":"0x116f480",
        "machine_condition":"CBZ W0,0x116F4D8",
        "zero_branch_target":"0x116f4d8",
        "conditional_branch_bytes":code[ZERO_BRANCH:ZERO_BRANCH+4].hex(),
        "file_open_result_w0_zero_path_syntactically_followed":True,
    }
    return {
        "status":"PINNED_FILEOPEN_ZERO_RETURN_TO_STATUS5_STATIC_PATHS",
        "original_main_sha256":digest,
        "file_open_zero_result_branch":witness,
        "first_status5":{
            "callsite":"0x116f520","target":"0x120661c",
            "reachable_from_CBZ_zero_taken":first is not None,
            "syntactic_path_offsets":[hex(a) for a in first] if first else None,
            "runtime_execution_proven":False
        },
        "second_status5":{
            "callsite":"0x116f5c0","target":"0x120661c",
            "reachable_from_CBZ_zero_taken":second is not None,
            "syntactic_path_offsets":[hex(a) for a in second] if second else None,
            "guarding_branch":"0x116f5b4 B.NE 0x116F5C4",
            "runtime_execution_proven":False
        },
        "all_branches_are_syntactic_and_calls_assumed_to_return":True,
        "actual_CRI_file_open_failure_tested":False,
        "real_file_load_failure_causes_status5_runtime_proven":False,
        "async_completion_verified":False,
        "unbind_and_archive_precedence_verified":False,
        "safe_trampoline_ABI_verified":False,
        "native_hook_added":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
