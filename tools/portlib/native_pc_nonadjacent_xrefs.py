"""Bounded nonadjacent ADRP/ADD evidence from exact SHA-pinned Switch 1.70 main.

No ABI, callback, ownership or runtime interpretation is inferred.
"""
import hashlib
import struct
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM, CS_GRP_JUMP, CS_GRP_CALL
from capstone.arm64 import ARM64_OP_REG, ARM64_OP_IMM
from .native_cpk_graph import MAIN_SHA256
from .nso_profile import segments
from .pc_api_manifest import ALL_FAMILIES


def candidate_pairs(text, base, targets, window=12):
    """Find syntactic ADRP -> ADD chains, stopping at clobbers/control flow."""
    if not 1 <= window <= 32:
        raise ValueError("Invalid instruction window")
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    results = []
    for offset in range(0, len(text)-3, 4):
        word = struct.unpack_from("<I", text, offset)[0]
        if word & 0x9f000000 != 0x90000000:
            continue
        pc = base + offset
        block = text[offset:offset + 4*(window+1)]
        ins = list(md.disasm(block, pc))
        if not ins or ins[0].mnemonic != "adrp":
            continue
        first = ins[0]
        if len(first.operands) != 2 or first.operands[1].type != ARM64_OP_IMM:
            continue
        reg = first.operands[0].reg
        page = first.operands[1].imm
        previous = pc
        for second in ins[1:]:
            if second.address != previous + 4:
                break
            previous = second.address
            if second.mnemonic == "add" and len(second.operands) == 3:
                dst, src, imm = second.operands
                if (dst.type == src.type == ARM64_OP_REG and src.reg == reg
                        and imm.type == ARM64_OP_IMM):
                    target = page + imm.imm
                    if target in targets:
                        results.append({"adrp": hex(pc), "add": hex(second.address),
                                        "target": hex(target), "names": targets[target]})
            _, writes = second.regs_access()
            if reg in writes or second.group(CS_GRP_JUMP) or second.group(CS_GRP_CALL) or second.mnemonic == "ret":
                break
    return results


def analyze(nso):
    sha = hashlib.sha256(nso).hexdigest()
    if sha != MAIN_SHA256:
        raise ValueError("Expected original SHA-pinned Switch 1.70 main")
    seg = segments(nso)
    base, text, _ = seg[0]
    targets = {}
    for name in sorted(ALL_FAMILIES):
        needle = name.encode("ascii") + b"\x00"
        for va, data, _ in seg:
            pos = 0
            while True:
                pos = data.find(needle, pos)
                if pos < 0:
                    break
                if pos == 0 or data[pos-1] == 0:
                    targets.setdefault(va+pos, []).append(name)
                pos += 1
    references = candidate_pairs(text, base, targets)
    return {"main_sha256": sha,
            "segment_sha256": [hashlib.sha256(data).hexdigest() for _, data, _ in seg],
            "literal_target_count": len(targets),
            "bounded_reference_count": len(references), "references": references,
            "max_instructions": 12,
            "scope": "Exact NUL ASCII family names; bounded nonadjacent ADRP/ADD, clobber/branch stop",
            "negative_results_are_not_proof_of_absence": True,
            "native_consumer_abi_verified": False, "ownership_lifecycle_verified": False,
            "archive_precedence_verified": False, "gameplay_verified": False}
