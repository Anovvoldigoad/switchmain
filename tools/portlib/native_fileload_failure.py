"""Read-only pinned native FileLoad error/status corridor disassembly.

A legacy *inactive diagnostic* in nsc_cpk_bridge.cpp describes a process
trampoline at 0x106F404, expecting A64 function prologue 0xA9BC7BFD.
Actual pinned original instruction is BL to 0xFFF6A0. This is a
fingerprint conflict, NOT permission to relocate/re-enable that hook.

Analyze the branch/error corridor including a previously proposed
file-open status-5 site around 0x106F4D8. Decode exact words; status,
data field ownership and native ABI must be justified independently.
"""
import hashlib
import struct
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from .native_cpk_graph import MAIN_SHA256,direct_branch
from .nso_profile import segments

CORRIDOR_START=0x106F450
CORRIDOR_END=0x106F570
LEGACY_PROCESS_CALLSITE=0x106F404
LEGACY_DIAGNOSTIC_EXPECTED_FIRST_WORD=0xA9BC7BFD
LEGACY_CALL_TARGET=0xFFF6A0
SOURCE_NAMED_FILE_OPEN_FAILURE=0x106F4D8


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Pinned original Switch 1.70 main is mandatory")
    rows=segments(nso)
    va,code,_=rows[0]
    if va or CORRIDOR_END>len(code) or LEGACY_PROCESS_CALLSITE+4>len(code):
        raise ValueError("Original code region out of bounds")
    old_word=struct.unpack_from("<I",code,LEGACY_PROCESS_CALLSITE)[0]
    actual_branch=direct_branch(old_word,LEGACY_PROCESS_CALLSITE)
    if actual_branch!=("BL",LEGACY_CALL_TARGET):
        raise ValueError("Corrected 0x106F404 direct BL proof no longer matches")
    if old_word==LEGACY_DIAGNOSTIC_EXPECTED_FIRST_WORD:
        raise ValueError("Legacy diagnostic mismatch suddenly disappeared; re-audit before use")
    decoder=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    decoder.skipdata=True
    raw=code[CORRIDOR_START:CORRIDOR_END]
    words=[]
    for ins in decoder.disasm(raw,CORRIDOR_START):
        if ins.size!=4:
            raise ValueError("Unexpected AArch64 decoded word size")
        original=code[ins.address:ins.address+4]
        if original!=bytes(ins.bytes):
            raise ValueError("Instruction bytes differ from original text")
        words.append({
            "at":f"0x{ins.address:x}",
            "bytes_le":original.hex(),
            "mnemonic":ins.mnemonic,
            "operands":ins.op_str,
        })
    if [int(w["at"],16) for w in words]!=list(range(CORRIDOR_START,CORRIDOR_END,4)):
        raise ValueError("Missing decoded or skipped instructions in corridor")
    selected=[]
    for ins in words:
        op=ins["operands"]
        if (ins["mnemonic"] in ("bl","blr","b","ret","cmp","cbz","cbnz",
                                "str","ldr","stur","ldur","mov","movz","movk")
            or ins["mnemonic"].startswith("b.")):
            selected.append(ins)
    point=next(x for x in words
               if int(x["at"],16)==SOURCE_NAMED_FILE_OPEN_FAILURE)
    return {
        "status":"PINNED_NATIVE_FILELOAD_ERROR_CORRIDOR_WORD_TRANSCRIPT_ONLY",
        "original_main_sha256":digest,
        "legacy_diagnostic_hook":{
            "source":"overlay/source/program/nsc_cpk_bridge.cpp",
            "old_named_process_offset":f"0x{LEGACY_PROCESS_CALLSITE:x}",
            "legacy_expected_prologue_word":f"0x{LEGACY_DIAGNOSTIC_EXPECTED_FIRST_WORD:08x}",
            "original_actual_word":f"0x{old_word:08x}",
            "actual_instruction":"BL",
            "actual_callee":f"0x{LEGACY_CALL_TARGET:x}",
            "source_fingerprint_matches_original_main":False,
            "unsafe_to_activate_legacy_trampoline_as_named":True,
            "whether_legacy_trampoline_is_active_at_runtime":"NOT_ESTABLISHED_BY_THIS_TEST"
        },
        "corridor":{"start":f"0x{CORRIDOR_START:x}",
                    "end_exclusive":f"0x{CORRIDOR_END:x}",
                    "raw_sha256":hashlib.sha256(raw).hexdigest(),
                    "word_count":len(words),
                    "instructions":words,
                    "selected_control_or_memory_words":selected,
                    "old_file_open_failure_comment_site":point},
        "status_5_branch_caused_by_file_open_failure_proven":False,
        "status_field_0x68_owner_proven":False,
        "read_context_error_field_0x1d8_proven":False,
        "calling_convention_or_CRI_async_proven":False,
        "safe_hook_relocation_or_installation_authorized":False,
        "native_hooks_added":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
