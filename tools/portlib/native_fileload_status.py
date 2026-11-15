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
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
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


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Exact pinned v1.70 original main required")
    rows=segments(nso)
    va,text,_=rows[0]
    if va!=0 or max(HELPER_WINDOW[1],OPEN_CORRIDOR[1])>len(text):
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
