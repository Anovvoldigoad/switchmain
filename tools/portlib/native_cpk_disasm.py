"""Read-only Capstone AArch64 instruction evidence at pinned CPK/FileLoad sites.

Unlike the earlier B/BL/BLR census, disassembles actual machine words around
the two observed BLR call sites, adjacent relocation-target code and verified
file-open direct call. This is only bounded linear disassembly; it does not
prove function boundaries, control flow, vtable ownership or native ABI.
No executable or CPK bytes are patched.
"""
import hashlib
import struct
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from .nso_profile import segments
from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_cpk_neighborhood import indirect_kind
from .native_cpk_pointer_tables import WITNESSES
from .native_cpk_indirect import _image_and_relocations, RELA_TYPE

# Exact offsets established in earlier Actions. Do not reinterpret as
# entrypoints: these include *mid-function* and virtual-method thunks.
SITES={
 "indirect_blr_1":(0x106ED9C,0x38,0x30),
 "indirect_blr_2":(0x106EDD0,0x38,0x30),
 "relocated_candidate_1":(0x106EDB8,0,0x60),
 "relocated_candidate_2":(0x106EDC4,0,0x60),
 "relocated_candidate_3":(0x106EDE0,0,0x60),
 "relocated_candidate_4":(0x106EDE8,0,0x60),
 "original_fileload_process_anchor":(0x106F404,0x20,0x80),
 "direct_file_open_caller":(0x116F47C,0x24,0x2c),
 "direct_file_open_target":(0x1170FB0,0,0x90),
}


def inspect(nso):
    h=hashlib.sha256(nso).hexdigest()
    if h!=MAIN_SHA256:
        raise ValueError("Exact hash-pinned NSC Switch v1.70 main required")
    segs,relocs=_image_and_relocations(nso)
    va,code,_=segs[0]
    if va!=0:
        raise ValueError("Unexpected NSO executable segment mapping")
    relative={(slot,addend) for slot,typ,addend in relocs if typ==RELA_TYPE}
    for pair in WITNESSES.items():
        if pair not in relative:
            raise ValueError("Previously observed relative pointer not present")
    observations={}
    for key,(anchor,left,right) in SITES.items():
        start=anchor-left
        size=left+right
        if start<0 or start%4 or size%4 or start+size>len(code):
            raise ValueError("Invalid bounded native disassembly range")
        raw=code[start:start+size]
        cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
        cs.skipdata=True
        instructions=[]
        for ins in cs.disasm(raw,start):
            if len(ins.bytes)!=4:
                raise ValueError("Unexpected AArch64 word width in pinned code")
            actual=code[ins.address:ins.address+4]
            if actual!=bytes(ins.bytes):
                raise ValueError("Disassembler instruction bytes mismatch")
            instructions.append({
                "code_offset":f"0x{ins.address:x}",
                "word_le":actual.hex(),
                "mnemonic":ins.mnemonic,
                "operands":ins.op_str,
                "raw_word_u32":struct.unpack("<I",actual)[0],
                "is_capstone_skipped_data":ins.mnemonic==".byte"
            })
        observed_offsets=[int(x["code_offset"],16) for x in instructions]
        if observed_offsets!=list(range(start,start+size,4)):
            raise ValueError("Disassembly is not a complete bounded word transcript")
        observations[key]={
            "anchor":f"0x{anchor:x}",
            "start":f"0x{start:x}",
            "length":size,
            "sha256_instructions_window":hashlib.sha256(raw).hexdigest(),
            "words":instructions,
            "bounded_window_is_not_function_extent":True,
            "linear_disassembly_is_not_execution_evidence":True
        }
    for key,at in (("indirect_blr_1",0x106ED9C),("indirect_blr_2",0x106EDD0)):
        word=struct.unpack_from("<I",code,at)[0]
        if indirect_kind(word)!="BLR":
            raise ValueError("Pinned indirect BLR witness mismatch")
        witness=next(w for w in observations[key]["words"]
                     if int(w["code_offset"],16)==at)
        if witness["mnemonic"].lower()!="blr":
            raise ValueError("Capstone BLR disassembly disagreement")
    direct=direct_branch(struct.unpack_from("<I",code,0x116F47C)[0],0x116F47C)
    if direct!=("BL",0x1170FB0):
        raise ValueError("Pinned native file-open BL witness mismatch")
    return {
        "status":"PASS_PINNED_STATIC_BOUNDED_CAPSTONE_AARCH64",
        "source_main_sha256":h,
        "capstone_disassembled_windows":len(observations),
        "known_code_pointer_relocation_witnesses":[
            {"slot":f"0x{slot:x}","target":f"0x{target:x}"}
            for slot,target in WITNESSES.items()],
        "known_blr_offsets":["0x106ed9c","0x106edd0"],
        "known_file_open_direct_edge":{"at":"0x116f47c","target":"0x1170fb0","kind":"BL"},
        "windows":observations,
        "vtable_class_or_method_indices_proven":False,
        "native_function_extents_proven":False,
        "calling_convention_register_semantics_proven":False,
        "CRI_async_completion_verified":False,
        "CRI_unbind_or_destructor_verified":False,
        "archive_lookup_priority_winner_verified":False,
        "native_hook_installed":False,
        "gameplay_verified":False,"full_moddingapi":False
    }
