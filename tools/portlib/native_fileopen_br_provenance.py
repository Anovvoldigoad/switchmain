"""Read-only backward register-def evidence at pinned FileOpen indirect branches.

This is a bounded *syntactic* def-use slice, not an interprocedural proof.
"""
import hashlib
import struct
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM, CS_GRP_JUMP, CS_GRP_CALL
from .native_cpk_graph import MAIN_SHA256
from .nso_profile import segments

SITES = {"fileopen_br_x1": (0x116B724, "x1"),
         "fileopen_br_x2": (0x116B430, "x2")}


def slice_site(code, base, site, expected_reg, limit=48):
    """Collect explicit reaching definitions until a control-flow boundary.

    Unknown memory contents, implicit state and path merges remain unresolved.
    """
    if not 1 <= limit <= 128 or site % 4 or site < base or site + 4 > base + len(code):
        raise ValueError("Invalid site/window")
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    start = max(base, site - limit * 4)
    start += (-start) % 4
    ins = list(md.disasm(code[start-base:site-base+4], start))
    if not ins or ins[-1].address != site or ins[-1].mnemonic != "br":
        raise ValueError("Expected indirect BR at pinned site")
    operand = ins[-1].op_str.strip().lower()
    if operand != expected_reg:
        raise ValueError("Indirect branch register differs from pinned expectation")
    wanted = {ins[-1].operands[0].reg}
    definitions = []
    boundary = "window_limit"
    for i in reversed(ins[:-1]):
        if i.group(CS_GRP_JUMP) or i.group(CS_GRP_CALL) or i.mnemonic in ("ret", "eret"):
            boundary = "control_flow_barrier"
            break
        reads, writes = i.regs_access()
        matched = wanted.intersection(writes)
        if not matched:
            continue
        definitions.append({"address": hex(i.address), "bytes_le": i.bytes.hex(),
                            "mnemonic": i.mnemonic, "operands": i.op_str,
                            "writes_required_register": True,
                            "reads": [md.reg_name(r) for r in reads],
                            "writes": [md.reg_name(r) for r in writes],
                            "memory_value_resolved": False})
        wanted.difference_update(matched)
        wanted.update(reads)
        if not wanted:
            boundary = "all_register_dependencies_accounted_for"
            break
    return {"site": hex(site), "branch_bytes_le": ins[-1].bytes.hex(),
            "branch_register": expected_reg, "definitions_reverse_order": definitions,
            "unresolved_registers": sorted(md.reg_name(r) for r in wanted),
            "stop_reason": boundary, "bounded_instructions": limit,
            "memory_dereferences_resolved": False,
            "cross_basic_block_proven": False,
            "engine_consumer_abi_verified": False}


def analyze(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original main SHA mismatch")
    rows = segments(nso)
    base, code, _ = rows[0]
    result = {}
    for name, (site, reg) in SITES.items():
        result[name] = slice_site(code, base, site, reg)
    return {"main_sha256": digest, "text_sha256": hashlib.sha256(code).hexdigest(),
            "sites": result, "scope": "bounded backward register definitions only",
            "ownership_verified": False, "async_verified": False,
            "archive_precedence_verified": False, "gameplay_verified": False}
