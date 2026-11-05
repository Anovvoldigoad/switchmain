"""Pinned ARM64 local structural facts for FileLoad-side BLR candidate calls.

This deliberately never labels these functions with CRI API semantics.
Machine-code facts:
  0x106ED90 LDR X8,[X20]
  0x106ED98 LDR X8,[X8,#0x20]
  0x106ED9C BLR X8
  0x106EDC8 LDR X8,[X0]
  0x106EDCC LDR X8,[X8,#0x10]
  0x106EDD0 BLR X8
  0x106F404 is a BL call IN an executable region, not a function start.
Earlier audit called 0x106F404 "fileload_process"; that was a guess.
Nearby 0x106F394 is the target of a separate R_AARCH64_RELATIVE
code relocation, and its first instruction is SUB SP,SP,#0x40:
a possible function entry but not runtime-verified.
"""
import hashlib
import struct
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_cpk_indirect import _image_and_relocations, RELA_TYPE

EXPECTED={
 0x106ED90:("ldr","x8, [x20]"),
 0x106ED98:("ldr","x8, [x8, #0x20]"),
 0x106ED9C:("blr","x8"),
 0x106EDC8:("ldr","x8, [x0]"),
 0x106EDCC:("ldr","x8, [x8, #0x10]"),
 0x106EDD0:("blr","x8"),
 0x106F394:("sub","sp, sp, #0x40"),
}
CANDIDATE_SLOT=0x215C478
CANDIDATE_TARGET=0x106F394
MISNAMED_LEGACY_ANCHOR=0x106F404
EXPECTED_CALL_TARGET=0xFFF6A0


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Not exact pinned v1.70 NSO main")
    segs,relocs=_image_and_relocations(nso)
    va,text,_=segs[0]
    if va or max(EXPECTED)+4>len(text):
        raise ValueError("Native code span mismatch")
    if (CANDIDATE_SLOT,RELA_TYPE,CANDIDATE_TARGET) not in relocs:
        raise ValueError("Pinned candidate entry relocation missing")
    decoder=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    witnesses=[]
    for at,(mnemonic,operands) in EXPECTED.items():
        word=text[at:at+4]
        seq=list(decoder.disasm(word,at))
        if len(seq)!=1 or seq[0].mnemonic!=mnemonic or seq[0].op_str!=operands:
            raise ValueError("Pinned architectural mnemonic/reg witness differs")
        witnesses.append({"offset":f"0x{at:x}",
                          "word_le":word.hex(),
                          "mnemonic":mnemonic,
                          "operands":operands})
    got=direct_branch(struct.unpack_from("<I",text,MISNAMED_LEGACY_ANCHOR)[0],
                      MISNAMED_LEGACY_ANCHOR)
    if got!=("BL",EXPECTED_CALL_TARGET):
        raise ValueError("Historical process anchor is not its pinned BL instruction")
    region=text[CANDIDATE_TARGET:MISNAMED_LEGACY_ANCHOR+0x44]
    digest_region=hashlib.sha256(region).hexdigest()
    return {
        "status":"PINNED_ARM64_REGISTER_DISPATCH_WITNESSES_ONLY",
        "main_sha256":digest,
        "source_region_start":f"0x{CANDIDATE_TARGET:x}",
        "source_region_sha256":digest_region,
        "witnesses":witnesses,
        "blr1_load_chain":["0x106ed90","0x106ed98","0x106ed9c"],
        "blr2_load_chain":["0x106edc8","0x106edcc","0x106edd0"],
        "possible_indirect_method_offsets_bytes":[0x20,0x10],
        "method_indices_not_proven":True,
        "candidate_entry_relocation":{
            "patch_slot":f"0x{CANDIDATE_SLOT:x}",
            "code_target":f"0x{CANDIDATE_TARGET:x}",
            "first_instruction":"sub sp, sp, #0x40",
            "function_entry_proven":False,
            "object_or_vtable_owner_proven":False,
        },
        "corrected_legacy_anchor":{
            "address":f"0x{MISNAMED_LEGACY_ANCHOR:x}",
            "instruction_kind":"BL",
            "call_target":f"0x{EXPECTED_CALL_TARGET:x}",
            "is_function_start_proven":False,
            "legacy_fileload_process_label_is_not_entrypoint_evidence":True,
        },
        "native_vtable_semantics_proven":False,
        "CRI_async_completion_verified":False,
        "CRI_archive_unbind_verified":False,
        "CRI_archive_lookup_precedence_verified":False,
        "ABI_verified":False,
        "runtime_hook_installed":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
