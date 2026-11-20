"""Find literal ARM64 code references to relocation-pair candidate bases.

Only adjacent ADRP/LDR and literal LDR addressing modes are considered.
A code reference to a candidate *slot* is not proof of the runtime X8 value.
"""
import hashlib
import json
import struct
from .native_cpk_graph import MAIN_SHA256
from .native_cpk_indirect import (_image_and_relocations, adrp_ldr_slot,
                                  ldr_literal_slot, RELA_TYPE)
from .native_fileopen_dispatch_relocations import candidate_pairs
from .native_fileopen_dispatch_objects import DISPATCHES


def referenced_bases(text, bases):
    """Return sorted (instruction RVA, base slot RVA, addressing mode)."""
    bases = set(bases)
    result = []
    for pc in range(0, len(text) - 3, 4):
        word = struct.unpack_from("<I", text, pc)[0]
        literal = ldr_literal_slot(word, pc)
        if literal in bases:
            result.append((pc, literal, "ldr_literal"))
        if pc + 8 <= len(text):
            following = struct.unpack_from("<I", text, pc + 4)[0]
            adjacent = adrp_ldr_slot(word, following, pc)
            if adjacent in bases:
                result.append((pc, adjacent, "adrp_ldr"))
    return sorted(set(result))


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    rows, records = _image_and_relocations(nso)
    if rows[0][0] != 0:
        raise ValueError("Unexpected original text RVA")
    text = rows[0][1]
    groups = []
    for site in DISPATCHES:
        pairs = candidate_pairs(records, len(text), site["offset"])
        bases = {int(pair["candidate_base"], 16) for pair in pairs}
        refs = referenced_bases(text, bases)
        serialized = json.dumps(refs, separators=(",", ":")).encode()
        groups.append({
            "dispatch_branch": hex(site["branch"]),
            "field_offset": site["offset"],
            "static_candidate_base_count": len(bases),
            "adjacent_instruction_reference_count": len(refs),
            "adjacent_instruction_references_sample": [
                {"instruction": hex(pc), "candidate_base": hex(base),
                 "mode": mode} for pc, base, mode in refs[:8]],
            "all_references_sha256": hashlib.sha256(serialized).hexdigest(),
            "sample_truncated": len(refs) > 8,
            "runtime_X8_base_proven": False,
        })
    return {
        "status": "ORIGINAL_MAIN_FILEOPEN_CANDIDATE_BASE_CODE_XREFS",
        "original_main_sha256": digest,
        "only_adjacent_adrp_ldr_and_literal_ldr": True,
        "dispatches": groups,
        "consumer_abi_proven": False,
        "ownership_lifecycle_async_unbind_proven": False,
        "archive_precedence_proven": False,
        "new_runtime_hook": False,
        "full_moddingapi": False,
        "ready_for_gameplay_test": False,
        "emulator_tested": False,
    }
