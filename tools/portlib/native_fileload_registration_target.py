"""SHA-pinned FileLoad registration code-pointer target evidence.

The relative relocation is treated as a link-time text offset only. The bounded
CFG is not a function extent and does not identify a destructor or authorize
a native hook.
"""
import hashlib
import struct
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_IMM, ARM64_OP_MEM

from .native_cpk_cfg import _edges
from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_fileload_guard_state import inspect as inspect_guard_state
from .native_fileopen_import import _read_image

WINDOW_BYTES = 0x100
MAX_REACHED = 256
RETURN_MNEMONICS = {"ret", "retaa", "retab"}


def _register_name(ins, register):
    if not register:
        return None
    name = ins.reg_name(register).lower()
    if name == "fp":
        return "x29"
    if name == "lr":
        return "x30"
    return name


def analyze_window(code, start, end, max_reached=MAX_REACHED):
    """Decode a bounded AArch64 window and walk only syntactic in-window edges."""
    if (not isinstance(start, int) or not isinstance(end, int)
            or start < 0 or end > len(code) or end <= start
            or (start & 3) or (end & 3)):
        raise ValueError("Invalid aligned registration-target analysis window")
    if not isinstance(max_reached, int) or max_reached <= 0:
        raise ValueError("Reachability budget must be positive")

    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True
    decoded = {}
    for pc in range(start, end, 4):
        raw = code[pc:pc + 4]
        rows = list(decoder.disasm(raw, pc))
        if len(rows) == 1 and rows[0].size == 4:
            decoded[pc] = rows[0]
    if start not in decoded:
        raise ValueError("Relocated target is not a decoded AArch64 instruction")

    queue = deque([start])
    reached = set()
    events = {}
    returns = set()
    direct_calls = set()
    indirect_calls = set()
    indirect_terminators = set()
    exits = set()
    undecodable = set()

    while queue:
        pc = queue.popleft()
        if pc in reached:
            continue
        if len(reached) >= max_reached:
            raise ValueError("Registration-target CFG node budget exceeded")
        ins = decoded.get(pc)
        if ins is None:
            undecodable.add(pc)
            reached.add(pc)
            continue
        reached.add(pc)
        try:
            reads, writes = ins.regs_access()
        except Exception as exc:
            raise ValueError("AArch64 register access decode failed at " + hex(pc)) from exc

        memory = []
        immediates = []
        for operand in ins.operands:
            if operand.type == ARM64_OP_MEM:
                memory.append({
                    "base_register": _register_name(ins, operand.mem.base),
                    "index_register": _register_name(ins, operand.mem.index),
                    "displacement": operand.mem.disp,
                    "access_size_bytes": operand.size,
                    "direction": ("write" if ins.mnemonic.startswith("st") else
                                  "read" if ins.mnemonic.startswith("ld") else "unknown"),
                    "writeback": bool(getattr(ins, "writeback", False)),
                })
            elif operand.type == ARM64_OP_IMM:
                immediates.append(hex(operand.imm) if operand.imm >= 0
                                  else "-" + hex(-operand.imm))

        row = {
            "pc": hex(pc),
            "word_le": code[pc:pc + 4].hex(),
            "mnemonic": ins.mnemonic,
            "operands": ins.op_str,
            "read_registers": sorted({_register_name(ins, r) for r in reads} - {None}),
            "written_registers": sorted({_register_name(ins, r) for r in writes} - {None}),
            "immediates": immediates,
            "memory_operands": memory,
            "successors": [],
        }
        for kind, target in _edges(pc, ins.mnemonic, ins.op_str):
            row["successors"].append({
                "kind": kind,
                "target": hex(target) if target is not None else None,
                "inside_analysis_window": (
                    start <= target < end if target is not None else None
                ),
            })
            if kind == "call" and target is not None:
                direct_calls.add((pc, target))
                continue
            if kind == "indirect_call_unresolved":
                indirect_calls.add(pc)
                continue
            if kind == "return_or_indirect_terminator":
                if ins.mnemonic in RETURN_MNEMONICS:
                    returns.add(pc)
                else:
                    indirect_terminators.add(pc)
                continue
            if target is None:
                exits.add((pc, kind, None))
            elif start <= target < end:
                queue.append(target)
            else:
                exits.add((pc, kind, target))
        events[pc] = row

    ordered = [events[pc] for pc in sorted(events)]
    memory_operands = [
        {"pc": row["pc"], **operand}
        for row in ordered for operand in row["memory_operands"]
    ]
    return {
        "window_start": hex(start),
        "window_end_exclusive": hex(end),
        "window_bytes": end - start,
        "window_sha256": hashlib.sha256(code[start:end]).hexdigest(),
        "reachable_decoded_words": len(ordered),
        "reached_undecodable_words": [hex(x) for x in sorted(undecodable)],
        "return_sites": [hex(x) for x in sorted(returns)],
        "direct_calls_not_walked": [
            {"site": hex(site), "target": hex(target)}
            for site, target in sorted(direct_calls)
        ],
        "unresolved_indirect_call_sites": [hex(x) for x in sorted(indirect_calls)],
        "indirect_terminators": [hex(x) for x in sorted(indirect_terminators)],
        "out_of_window_or_unknown_edges": [
            {"from": hex(pc), "kind": kind,
             "target": hex(target) if target is not None else None}
            for pc, kind, target in sorted(
                exits, key=lambda x: (x[0], x[1], x[2] or 0)
            )
        ],
        "memory_operands": memory_operands,
        "decoded_reachable_instructions": ordered,
        "bounded_window_not_function_extent": True,
        "direct_call_targets_not_walked": True,
        "indirect_targets_unresolved": True,
    }


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")

    guard_report = inspect_guard_state(nso)
    cell = guard_report["registration_helper_candidate"]["register_setup"]["x0"]["cell_evidence"]
    relocations = cell["relocations"]
    if len(relocations) != 1:
        raise ValueError("Registration pointer cell must have exactly one relocation")
    relocation = relocations[0]
    if (relocation.get("type_name") != "R_AARCH64_RELATIVE"
            or relocation.get("symbol_index") != 0
            or relocation.get("addend") != 0x116B888):
        raise ValueError("Pinned registration pointer relocation changed")

    rows, _memory = _read_image(nso)
    if len(rows) != 3 or rows[0][0] != 0:
        raise ValueError("Original NSO text layout changed")
    text = rows[0][1]
    target = relocation["addend"]
    if target & 3 or target + WINDOW_BYTES > len(text):
        raise ValueError("Relocated code-pointer target is outside bounded text window")

    cfg = analyze_window(text, target, target + WINDOW_BYTES)
    branch_word_candidates = []
    for pc in range(0, len(text) - 3, 4):
        branch = direct_branch(struct.unpack_from("<I", text, pc)[0], pc)
        if branch is not None and branch[1] == target:
            branch_word_candidates.append({"site": hex(pc), "branch_kind": branch[0]})

    return {
        "status": "PINNED_FILELOAD_RELOCATED_CODE_TARGET_STATIC_CFG_ONLY",
        "original_main_sha256": digest,
        "registration_pointer_cell": cell["address"],
        "relative_relocation": {
            "table": relocation["table"],
            "record_offset": relocation["relocation_record_offset"],
            "slot": relocation["slot"],
            "type_name": relocation["type_name"],
            "symbol_index": relocation["symbol_index"],
            "addend": hex(target),
            "addend_is_link_time_text_offset": True,
            "runtime_relocated_pointer_value_verified": False,
        },
        "target": {
            "address": hex(target),
            "region": "text",
            "window": cfg,
            "aligned_text_word_direct_B_BL_candidates": branch_word_candidates,
            "raw_aligned_word_census_only": True,
            "target_is_callback_candidate_only": True,
            "callback_invocation_verified": False,
            "destructor_identity_verified": False,
            "function_extent_verified": False,
        },
        "limits": {
            "registration_helper_identity_verified": False,
            "registration_table_runtime_target_verified": False,
            "callback_identity_verified": False,
            "destructor_identity_verified": False,
            "object_ownership_lifecycle_verified": False,
            "async_rollback_unbind_verified": False,
            "native_consumer_abi_verified": False,
            "archive_precedence_verified": False,
            "native_hook_added": False,
            "gameplay_verified": False,
            "full_moddingapi": False,
            "ready_for_gameplay_test": False,
            "emulator_tested": False,
        },
    }


if __name__ == "__main__":
    raise SystemExit("Use tests/test_native_fileload_registration_target.py")
