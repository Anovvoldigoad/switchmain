"""SHA-pinned bounded trace of the FileLoad registration table's direct callee.

The callsite is verified from the original main's bounded registration-target CFG.
This module records static control/data-flow evidence only; it does not identify a
callback, destructor, object type, ownership policy, or native consumer ABI.
"""
import hashlib
import struct
from collections import Counter

from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_fileopen_import import _read_image
from .native_fileload_registration_target import (
    analyze_window,
    inspect as inspect_registration_target,
)

CALL_SITE = 0x116B8A4
CALLER_LOAD_SITE = 0x116B8A0
CALLEE_TARGET = 0x116B390
WINDOW_BYTES = 0x200


def _hex(value):
    return "0x%x" % value


def _summary(cfg):
    instructions = cfg["decoded_reachable_instructions"]
    reads = Counter()
    writes = Counter()
    for row in instructions:
        reads.update(row["read_registers"])
        writes.update(row["written_registers"])

    memory = cfg["memory_operands"]
    return {
        "register_access_counts": {
            name: {"reads": reads[name], "writes": writes[name]}
            for name in sorted(set(reads) | set(writes))
        },
        "argument_register_access_counts": {
            "x%d" % index: {
                "reads": reads["x%d" % index],
                "writes": writes["x%d" % index],
            }
            for index in range(8)
        },
        "x0_observations": {
            "read_sites": [
                row["pc"] for row in instructions
                if "x0" in row["read_registers"]
            ],
            "write_sites": [
                row["pc"] for row in instructions
                if "x0" in row["written_registers"]
            ],
            "memory_base_sites": [
                item["pc"] for item in memory
                if item["base_register"] == "x0"
            ],
            "memory_index_sites": [
                item["pc"] for item in memory
                if item["index_register"] == "x0"
            ],
        },
        "stack_memory_operands": [
            item for item in memory
            if item["base_register"] in {"sp", "x29"}
            or item["index_register"] in {"sp", "x29"}
        ],
        "memory_operand_count": len(memory),
        "direct_call_count": len(cfg["direct_calls_not_walked"]),
        "unresolved_indirect_call_count": len(
            cfg["unresolved_indirect_call_sites"]
        ),
        "indirect_terminator_count": len(cfg["indirect_terminators"]),
        "return_count": len(cfg["return_sites"]),
        "out_of_window_or_unknown_edge_count": len(
            cfg["out_of_window_or_unknown_edges"]
        ),
    }


def analyze_callee(text, call_site, target, window_bytes=WINDOW_BYTES):
    """Trace one exact BL target in a bounded text window, never as a full function."""
    if not isinstance(text, (bytes, bytearray, memoryview)):
        raise ValueError("AArch64 text must be bytes-like")
    if (not isinstance(call_site, int) or not isinstance(target, int)
            or call_site < 0 or target < 0
            or (call_site & 3) or (target & 3)
            or call_site + 4 > len(text)):
        raise ValueError("Invalid aligned direct-call site or target")
    if (not isinstance(window_bytes, int) or window_bytes <= 0
            or (window_bytes & 3) or target + window_bytes > len(text)):
        raise ValueError("Callee analysis window is outside aligned text")

    word = struct.unpack_from("<I", text, call_site)[0]
    branch = direct_branch(word, call_site)
    if branch != ("BL", target):
        raise ValueError("Pinned callsite is not the expected direct BL target")

    cfg = analyze_window(text, target, target + window_bytes)
    inbound = []
    for pc in range(0, len(text) - 3, 4):
        candidate = direct_branch(struct.unpack_from("<I", text, pc)[0], pc)
        if candidate is not None and candidate[1] == target:
            inbound.append({
                "site": _hex(pc),
                "branch_kind": candidate[0],
            })

    if not any(row["site"] == _hex(call_site)
               and row["branch_kind"] == "BL" for row in inbound):
        raise ValueError("Verified caller BL is absent from raw inbound census")

    return {
        "call_site": _hex(call_site),
        "call_site_word_le": bytes(text[call_site:call_site + 4]).hex(),
        "target": _hex(target),
        "window": cfg,
        "summary": _summary(cfg),
        "raw_aligned_text_B_BL_inbound_candidates": inbound,
        "raw_inbound_census_is_not_function_or_callback_proof": True,
        "function_extent_verified": False,
    }


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")

    registration = inspect_registration_target(nso)
    caller_cfg = registration["target"]["window"]
    expected_edge = {"site": _hex(CALL_SITE), "target": _hex(CALLEE_TARGET)}
    if expected_edge not in caller_cfg["direct_calls_not_walked"]:
        raise ValueError("Pinned registration CFG no longer contains expected BL edge")

    caller_row = next(
        (row for row in caller_cfg["decoded_reachable_instructions"]
         if row["pc"] == _hex(CALLER_LOAD_SITE)),
        None,
    )
    if caller_row is None or "x0" not in caller_row["written_registers"]:
        raise ValueError("Expected caller X0 load is not decoded at the pinned site")
    source_operands = [
        item for item in caller_row["memory_operands"]
        if item["base_register"] == "x8"
        and item["index_register"] is None
        and item["displacement"] == 0x28
        and item["access_size_bytes"] == 8
        and item["direction"] == "read"
    ]
    if len(source_operands) != 1:
        raise ValueError("Expected single 64-bit X8+0x28 caller load is absent")

    rows, _memory = _read_image(nso)
    if len(rows) != 3 or rows[0][0] != 0:
        raise ValueError("Original NSO text layout changed")
    text = rows[0][1]
    callee = analyze_callee(text, CALL_SITE, CALLEE_TARGET)

    return {
        "status": "PINNED_FILELOAD_REGISTRATION_CALLEE_STATIC_TRACE_ONLY",
        "original_main_sha256": digest,
        "caller": {
            "load_site": _hex(CALLER_LOAD_SITE),
            "load_mnemonic": caller_row["mnemonic"],
            "load_operands": caller_row["operands"],
            "load_memory_operand": source_operands[0],
            "direct_call_site": _hex(CALL_SITE),
            "direct_call_target": _hex(CALLEE_TARGET),
            "x0_value_type_verified": False,
        },
        "callee": callee,
        "limits": {
            "callback_invocation_verified": False,
            "callback_identity_verified": False,
            "destructor_identity_verified": False,
            "object_type_verified": False,
            "ownership_lifecycle_verified": False,
            "lock_unlock_semantics_verified": False,
            "async_behavior_verified": False,
            "rollback_unbind_verified": False,
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
    raise SystemExit("Use tests/test_native_fileload_registration_callee.py")
