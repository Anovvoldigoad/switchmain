"""SHA-pinned native main: literal and ADRP/ADD xrefs for nine PC API families.

A literal/xref is evidence of a reference, not a consumer ABI or invocation.
"""
import hashlib
import struct
from .nso_profile import segments
from .native_cpk_graph import MAIN_SHA256
from .pc_api_manifest import ALL_FAMILIES

def adrp_add_target(adrp, add, pc):
    """Return the referenced virtual address only for matching ADRP + ADD imm."""
    if adrp & 0x9f000000 != 0x90000000 or add & 0xffc00000 != 0x91000000:
        return None
    reg = adrp & 31
    if (add >> 5) & 31 != reg or add & 31 != reg:
        return None
    imm = ((adrp >> 5) & 0x7ffff) << 2 | ((adrp >> 29) & 3)
    if imm & (1 << 20):
        imm -= 1 << 21
    page = (pc & ~4095) + (imm << 12)
    return page + (((add >> 10) & 4095) << (12 if add & 0x400000 else 0))

def scan(nso):
    sha = hashlib.sha256(nso).hexdigest()
    if sha != MAIN_SHA256:
        raise ValueError("Expected original SHA-pinned Switch 1.70 main")
    seg = segments(nso)
    text_va, text, _ = seg[0]
    # Only complete NUL-terminated ASCII family names count as literal matches.
    names = sorted(ALL_FAMILIES)
    hits = {}
    for name in names:
        pattern = name.encode("ascii") + b"\x00"
        locations = []
        for index, (va, data, _) in enumerate(seg):
            pos = 0
            while True:
                pos = data.find(pattern, pos)
                if pos < 0:
                    break
                if pos == 0 or data[pos - 1] == 0:
                    locations.append({"segment": index, "va": va + pos})
                pos += 1
        hits[name] = locations
    target_names = {}
    for name, locations in hits.items():
        for loc in locations:
            target_names.setdefault(loc["va"], []).append(name)
    references = []
    # This deliberately checks only adjacent, register-matched ADRP/ADD.
    # Nonadjacent address materialization, LDR, GOT and indirect uses remain unresolved.
    for pos in range(0, len(text) - 7, 4):
        first, second = struct.unpack_from("<II", text, pos)
        target = adrp_add_target(first, second, text_va + pos)
        if target in target_names:
            references.append({"pc": hex(text_va + pos), "target": hex(target),
                               "families": target_names[target]})
    return {
        "status": "PINNED_MAIN_LITERAL_ADRP_ADD_CENSUS_NOT_CONSUMER_PROOF",
        "main_sha256": sha,
        "segment_sha256": [hashlib.sha256(data).hexdigest() for _, data, _ in seg],
        "family_count": len(names),
        "families": {name: {"literal_locations": [hex(x["va"]) for x in hits[name]],
                              "adjacent_adrp_add_references": [x["pc"] for x in references if name in x["families"]]}
                     for name in names},
        "direct_reference_count": len(references),
        "scope": "NUL-terminated exact ASCII names; adjacent register-matched ADRP/ADD only",
        "negative_results_are_not_proof_of_absence": True,
        "native_consumer_abi_verified": False,
        "ownership_lifecycle_verified": False,
        "archive_precedence_verified": False,
        "gameplay_verified": False,
    }
