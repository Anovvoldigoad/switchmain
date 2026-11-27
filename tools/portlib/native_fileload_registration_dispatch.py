"""Static data-flow proof for the FileLoad registration callee's indirect tail branch.

This is pinned to the original Switch v1.70 main. It follows only exact
instructions/edges already observed in the bounded callee trace; it does not
identify a vtable, callback, destructor, object type, or engine ABI.
"""
import hashlib
import struct

from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_fileopen_import import _read_image
from .native_fileload_registration_target import analyze_window
from .native_fileload_registration_callee import inspect as inspect_callee, _summary

WINDOW_BYTES = 0x100
EXPECTED_DIRECT_CALLS = {
    0x116B39C: 0x116B7B0,
    0x116B3A4: 0x116D380,
    0x116B3B0: 0x116B82C,
}
EXPECTED_ALTERNATE_BRANCH = (0x116B3EC, 0x116D820)


def _hex(value):
    return "0x%x" % value


def _inbound_candidates(text, targets):
    wanted = set(targets)
    found = {target: [] for target in wanted}
    for pc in range(0, len(text) - 3, 4):
        branch = direct_branch(struct.unpack_from("<I", text, pc)[0], pc)
        if branch is not None and branch[1] in wanted:
            found[branch[1]].append({
                "site": _hex(pc),
                "branch_kind": branch[0],
            })
    return found


def _trace_target(text, target, inbound, window_bytes):
    cfg = analyze_window(text, target, target + window_bytes)
    return {
        "target": _hex(target),
        "window": cfg,
        "summary": _summary(cfg),
        "raw_aligned_text_B_BL_inbound_candidates": inbound,
        "raw_inbound_census_is_not_function_extent_proof": True,
        "function_extent_verified": False,
    }


def trace_target(text, target, window_bytes=WINDOW_BYTES):
    """Trace a bounded code window reached by a verified direct edge."""
    if not isinstance(text, (bytes, bytearray, memoryview)):
        raise ValueError("AArch64 text must be bytes-like")
    if (not isinstance(target, int) or target < 0 or (target & 3)
            or not isinstance(window_bytes, int) or window_bytes <= 0
            or (window_bytes & 3) or target + window_bytes > len(text)):
        raise ValueError("Invalid bounded direct-target window")
    inbound = _inbound_candidates(text, (target,))[target]
    return _trace_target(text, target, inbound, window_bytes)


def _row(rows, address, mnemonic, operands):
    result = rows.get(_hex(address))
    if (result is None or result["mnemonic"] != mnemonic
            or result["operands"] != operands):
        raise ValueError("Pinned dispatch instruction changed at " + _hex(address))
    return result


def _memory(row, base, displacement, direction):
    matches = [
        item for item in row["memory_operands"]
        if item["base_register"] == base
        and item["index_register"] is None
        and item["displacement"] == displacement
        and item["access_size_bytes"] == 8
        and item["direction"] == direction
        and item["writeback"] is False
    ]
    if len(matches) != 1:
        raise ValueError("Pinned 64-bit memory source changed at " + row["pc"])
    return matches[0]


def extract_dispatch_flow(cfg):
    """Validate the exact X19/X20/X0/X1/X2 sequence and conditional exits."""
    rows = {row["pc"]: row for row in cfg["decoded_reachable_instructions"]}
    expected = [
        (0x116B390, "str", "x30, [sp, #-0x20]!"),
        (0x116B394, "stp", "x20, x19, [sp, #0x10]"),
        (0x116B398, "mov", "x19, x0"),
        (0x116B39C, "bl", "#0x116b7b0"),
        (0x116B3A0, "mov", "x20, x0"),
        (0x116B3A4, "bl", "#0x116d380"),
        (0x116B3A8, "mov", "w1, w0"),
        (0x116B3AC, "mov", "x0, x20"),
        (0x116B3B0, "bl", "#0x116b82c"),
        (0x116B3B4, "cbz", "x19, #0x116b3d4"),
        (0x116B3B8, "cbz", "x0, #0x116b3e0"),
        (0x116B3BC, "ldr", "x8, [x0]"),
        (0x116B3C0, "mov", "x1, x19"),
        (0x116B3C4, "ldr", "x2, [x8, #0x58]"),
        (0x116B3C8, "ldp", "x20, x19, [sp, #0x10]"),
        (0x116B3CC, "ldr", "x30, [sp], #0x20"),
        (0x116B3D0, "br", "x2"),
        (0x116B3D4, "ldp", "x20, x19, [sp, #0x10]"),
        (0x116B3D8, "ldr", "x30, [sp], #0x20"),
        (0x116B3DC, "ret", ""),
        (0x116B3E0, "mov", "x0, x19"),
        (0x116B3E4, "ldp", "x20, x19, [sp, #0x10]"),
        (0x116B3E8, "ldr", "x30, [sp], #0x20"),
        (0x116B3EC, "b", "#0x116d820"),
    ]
    checked = {}
    for address, mnemonic, operands in expected:
        checked[address] = _row(rows, address, mnemonic, operands)

    for site, target in EXPECTED_DIRECT_CALLS.items():
        edge = {"kind": "call", "target": _hex(target), "inside_analysis_window": False}
        if edge not in checked[site]["successors"]:
            raise ValueError("Expected direct call edge changed at " + _hex(site))

    if checked[0x116B3B4]["successors"] != [
        {"kind": "conditional", "target": "0x116b3d4", "inside_analysis_window": True},
        {"kind": "fallthrough", "target": "0x116b3b8", "inside_analysis_window": True},
    ]:
        raise ValueError("X19 conditional path changed")
    if checked[0x116B3B8]["successors"] != [
        {"kind": "conditional", "target": "0x116b3e0", "inside_analysis_window": True},
        {"kind": "fallthrough", "target": "0x116b3bc", "inside_analysis_window": True},
    ]:
        raise ValueError("X0 conditional path changed")
    if checked[0x116B3D0]["successors"] != [{
        "kind": "return_or_indirect_terminator",
        "target": None,
        "inside_analysis_window": None,
    }]:
        raise ValueError("Indirect BR X2 terminator changed")
    if checked[0x116B3EC]["successors"] != [{
        "kind": "unconditional",
        "target": _hex(EXPECTED_ALTERNATE_BRANCH[1]),
        "inside_analysis_window": False,
    }]:
        raise ValueError("Alternate branch target changed")

    x0_to_x8 = _memory(checked[0x116B3BC], "x0", 0, "read")
    x8_to_x2 = _memory(checked[0x116B3C4], "x8", 0x58, "read")
    if ("x0" not in checked[0x116B398]["read_registers"]
            or "x19" not in checked[0x116B398]["written_registers"]):
        raise ValueError("Entry X0 -> X19 move changed")
    if ("x19" not in checked[0x116B3C0]["read_registers"]
            or "x1" not in checked[0x116B3C0]["written_registers"]):
        raise ValueError("X19 -> X1 move changed")
    if "x2" not in checked[0x116B3D0]["read_registers"]:
        raise ValueError("BR X2 no longer reads X2")
    if any("x0" in checked[address]["written_registers"]
           for address in (0x116B3B4, 0x116B3B8)):
        raise ValueError("X0 is explicitly overwritten between third BL and dereference")

    return {
        "entry_register_flow": {
            "source_register": "x0",
            "destination_register": "x19",
            "site": _hex(0x116B398),
            "value_type_verified": False,
        },
        "direct_call_sequence": [
            {
                "site": _hex(0x116B39C),
                "target": _hex(0x116B7B0),
                "x0_source_before_call": "entry_x0",
            },
            {
                "site": _hex(0x116B3A4),
                "target": _hex(0x116D380),
                "x0_source_before_call": "x20_from_post_call_x0_at_0x116b39c",
            },
            {
                "site": _hex(0x116B3B0),
                "target": _hex(0x116B82C),
                "x0_source_before_call": "x20",
                "x1_source_before_call": "w0_from_post_call_result_at_0x116b3a4",
            },
        ],
        "indirect_tail_branch": {
            "site": _hex(0x116B3D0),
            "mnemonic": "br",
            "target_register": "x2",
            "x2_load_site": _hex(0x116B3C4),
            "x2_memory_source": x8_to_x2,
            "x8_load_site": _hex(0x116B3BC),
            "x8_memory_source": x0_to_x8,
            "x0_before_x8_load": "post_BL_X0_with_only_CBZ_reads_between_BL_at_0x116b3b0_and_LDR_at_0x116b3bc",
            "x1_load_site": _hex(0x116B3C0),
            "x1_source_register": "x19",
            "branch_target_resolved": False,
            "callback_identity_verified": False,
            "vtable_identity_verified": False,
        },
        "conditional_paths": {
            "cbz_x19_site": _hex(0x116B3B4),
            "cbz_x19_target": _hex(0x116B3D4),
            "cbz_x0_site": _hex(0x116B3B8),
            "cbz_x0_target": _hex(0x116B3E0),
            "alternate_branch_site": _hex(EXPECTED_ALTERNATE_BRANCH[0]),
            "alternate_branch_target": _hex(EXPECTED_ALTERNATE_BRANCH[1]),
            "alternate_path_x0_source": "x19",
            "return_site": _hex(0x116B3DC),
        },
        "stack_observations": {
            "entry_sp_writeback_site": _hex(0x116B390),
            "entry_sp_displacement": -0x20,
            "saved_x20_x19_site": _hex(0x116B394),
            "saved_x20_x19_offset": 0x10,
            "normal_restore_pair_site": _hex(0x116B3C8),
            "normal_restore_lr_site": _hex(0x116B3CC),
            "alternate_restore_pair_site": _hex(0x116B3D4),
            "alternate_restore_lr_site": _hex(0x116B3D8),
            "stack_frame_size_observed": 0x20,
            "stack_frame_is_complete_function_proof": False,
        },
    }


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")

    callee_report = inspect_callee(nso)
    flow = extract_dispatch_flow(callee_report["callee"]["window"])
    rows, _memory = _read_image(nso)
    if len(rows) != 3 or rows[0][0] != 0:
        raise ValueError("Original NSO text layout changed")
    text = rows[0][1]

    targets = list(EXPECTED_DIRECT_CALLS.values()) + [EXPECTED_ALTERNATE_BRANCH[1]]
    inbound = _inbound_candidates(text, targets)
    target_traces = {
        _hex(target): _trace_target(text, target, inbound[target], WINDOW_BYTES)
        for target in targets
    }

    return {
        "status": "PINNED_FILELOAD_REGISTRATION_DISPATCH_STATIC_TRACE_ONLY",
        "original_main_sha256": digest,
        "callee_target": callee_report["callee"]["target"],
        "callee_window_sha256": callee_report["callee"]["window"]["window_sha256"],
        "dispatch_flow": flow,
        "bounded_target_traces": target_traces,
        "limits": {
            "indirect_branch_target_resolved": False,
            "callback_identity_verified": False,
            "vtable_identity_verified": False,
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
    raise SystemExit("Use tests/test_native_fileload_registration_dispatch.py")
