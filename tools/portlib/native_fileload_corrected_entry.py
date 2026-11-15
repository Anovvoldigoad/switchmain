"""Original SHA-locked audit of a likely 0x100000 legacy FileLoad offset error.

The dormant InstallTraceHooks in nsc_cpk_bridge.cpp fingerprints
kLoadRequestProcessOffset = 0x106F404 using *function prologue* words
A9BC7BFD A9015FF8 A90257F6 A9034FF4 ...
But original main+0x106F404 is a BL call; earlier research corrected that.

The same legacy source quotes FileLoad callsite 0x116F29C, native
file-open BL caller 0x116F47C and failure branches 0x116F520/5C0.
This tool independently tests the 0x116F404 hypothesis against original
main bytes, without editing/installing any hook. Function extent,
native ABI, state field meaning and CRI lifecycle still require proof.
"""
import hashlib
import struct
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from .native_cpk_graph import MAIN_SHA256,direct_branch
from .nso_profile import segments

LEGACY_MISLOCATED=0x106F404
NEW_CANDIDATE=0x116F404
RECORDED_PROLOGUE=(
    0xA9BC7BFD,0xA9015FF8,0xA90257F6,0xA9034FF4,
    0xD10A03FF,0xD0019008,0xB9807058,0xAA0003F5,
)
COMMENTED_CALLSITE=0x116F29C
FILE_OPEN_CALLSITE=0x116F47C
FILE_OPEN_TARGET=0x1170FB0
COMMENTED_FAILURE_SITES=(0x116F520,0x116F5C0)
WINDOW=(0x116F3E0,0x116F650)


def _disassemble_words(text,start,end):
    dis=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    rows=[]
    for at in range(start,end,4):
        raw=text[at:at+4]
        one=list(dis.disasm(raw,at))
        rows.append({
            "at":f"0x{at:x}",
            "word_le":raw.hex(),
            "u32_hex":f"0x{struct.unpack('<I',raw)[0]:08x}",
            "mnemonic":one[0].mnemonic if one and one[0].size==4 else "UNPARSED_A64",
            "operands":one[0].op_str if one and one[0].size==4 else "",
        })
    return rows


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Wrong SHA-pinned Switch 1.70 main")
    rows=segments(nso)
    va,code,_=rows[0]
    if va or WINDOW[1]>len(code):
        raise ValueError("Wrong original executable geometry")
    observed=struct.unpack_from("<8I",code,NEW_CANDIDATE)
    if observed!=RECORDED_PROLOGUE:
        raise ValueError("Corrected 0x116F404 candidate does NOT match recorded source prologue")
    legacy=direct_branch(struct.unpack_from("<I",code,LEGACY_MISLOCATED)[0],LEGACY_MISLOCATED)
    if legacy!=("BL",0xFFF6A0):
        raise ValueError("Prior 0x106F404 BL correction not reproducible")
    fileopen=direct_branch(struct.unpack_from("<I",code,FILE_OPEN_CALLSITE)[0],FILE_OPEN_CALLSITE)
    if fileopen!=("BL",FILE_OPEN_TARGET):
        raise ValueError("Known FileOpen native BL witness disagrees")
    caller=direct_branch(struct.unpack_from("<I",code,COMMENTED_CALLSITE)[0],COMMENTED_CALLSITE)
    ins=_disassemble_words(code,*WINDOW)
    named={f"0x{at:x}":next(v for v in ins if int(v["at"],16)==at)
           for at in COMMENTED_FAILURE_SITES}
    return {
        "status":"PINNED_SOURCE_PROLOGUE_MATCH_AT_CORRECTED_NATIVE_FILELOAD_ADDRESS",
        "main_sha256":digest,
        "source":"overlay/source/program/nsc_cpk_bridge.cpp dormant InstallTraceHooks",
        "legacy_mislocated_hook_candidate":f"0x{LEGACY_MISLOCATED:x}",
        "legacy_actual":{"kind":legacy[0],"target":f"0x{legacy[1]:x}"},
        "source_prologue_word_count":len(RECORDED_PROLOGUE),
        "prologue_candidate_verified":f"0x{NEW_CANDIDATE:x}",
        "prologue_words_match_original_main":True,
        "offset_discrepancy_bytes":NEW_CANDIDATE-LEGACY_MISLOCATED,
        "commented_inbound_site":{
            "at":f"0x{COMMENTED_CALLSITE:x}",
            "actual_branch_kind":caller[0] if caller else None,
            "actual_branch_target":f"0x{caller[1]:x}" if caller else None,
            "is_direct_BL_to_candidate":caller==("BL",NEW_CANDIDATE)
        },
        "native_file_open_edge":{
            "at":f"0x{FILE_OPEN_CALLSITE:x}",
            "target":f"0x{FILE_OPEN_TARGET:x}",
            "branch_kind":"BL",
            "within_candidate_analysis_window":True
        },
        "commented_failure_locations_words":named,
        "nearby_instruction_window":{
            "start":f"0x{WINDOW[0]:x}",
            "end_exclusive":f"0x{WINDOW[1]:x}",
            "sha256":hashlib.sha256(code[WINDOW[0]:WINDOW[1]]).hexdigest(),
            "instruction_count":len(ins),
            "words":ins
        },
        "prologue_not_full_function_extent_proof":True,
        "AAPCS64_argument_semantics_verified":False,
        "read_error_offset_and_status_5_ownership_verified":False,
        "async_completion_proven":False,
        "unbind_destructor_proven":False,
        "runtime_archive_priority_winner_proven":False,
        "legacy_hook_was_relocated_or_enabled":False,
        "new_native_hook_installed":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
