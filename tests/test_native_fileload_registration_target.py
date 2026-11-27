"""Synthetic CFG and SHA-pinned FileLoad registration-target regressions."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_registration_target import analyze_window, inspect


def expect_reject(fn, label):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(label + " was accepted")


def words(*values):
    return struct.pack("<" + "I" * len(values), *values)


def synthetic_cfg():
    # BL target is recorded but not walked; only the return fallthrough is reachable.
    direct = analyze_window(
        words(0x94000002, 0xD65F03C0, 0xF9000020, 0xD65F03C0), 0, 16
    )
    assert direct["direct_calls_not_walked"] == [{"site": "0x0", "target": "0x8"}]
    assert direct["return_sites"] == ["0x4"]
    assert [x["pc"] for x in direct["decoded_reachable_instructions"]] == ["0x0", "0x4"]
    assert direct["bounded_window_not_function_extent"] is True

    # Conditional edges visit both target and fallthrough; converged nodes deduplicate.
    conditional = analyze_window(
        words(0x54000040, 0xD65F03C0, 0xD65F03C0, 0xD65F03C0), 0, 16
    )
    assert conditional["return_sites"] == ["0x4", "0x8"]
    assert conditional["reachable_decoded_words"] == 3

    # A branch outside the supplied window is recorded and never followed.
    external = analyze_window(
        words(0x14000010, 0xD65F03C0, 0xD65F03C0, 0xD65F03C0), 0, 16
    )
    assert external["return_sites"] == []
    assert external["out_of_window_or_unknown_edges"] == [
        {"from": "0x0", "kind": "unconditional", "target": "0x40"}
    ]

    # Memory width/base and unresolved indirect calls are explicit, not inferred.
    memory = analyze_window(words(0xF9000020, 0xD65F03C0), 0, 8)
    assert memory["memory_operands"] == [{
        "pc": "0x0", "base_register": "x1", "index_register": None,
        "displacement": 0, "access_size_bytes": 8,
        "direction": "write", "writeback": False,
    }]
    indirect = analyze_window(words(0xD63F0100, 0xD65F03C0), 0, 8)
    assert indirect["unresolved_indirect_call_sites"] == ["0x0"]
    assert indirect["return_sites"] == ["0x4"]

    # The window boundary and work budget are fail-closed.
    expect_reject(lambda: analyze_window(words(0xD65F03C0, 0xD65F03C0), 0, 7),
                  "unaligned end")
    expect_reject(lambda: analyze_window(words(0xD65F03C0), 4, 8),
                  "missing entry")
    expect_reject(lambda: analyze_window(words(0x54000040, 0xD65F03C0,
                                               0xD65F03C0, 0xD65F03C0),
                                         0, 16, max_reached=1),
                  "reachability budget")


def run(main, output):
    synthetic_cfg()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["registration_pointer_cell"] == "0x215d2b0"
    assert report["relative_relocation"] == {
        "table": "DT_RELA",
        "record_offset": "0x1976d80",
        "slot": "0x215d2b0",
        "type_name": "R_AARCH64_RELATIVE",
        "symbol_index": 0,
        "addend": "0x116b888",
        "addend_is_link_time_text_offset": True,
        "runtime_relocated_pointer_value_verified": False,
    }
    target = report["target"]
    assert target["address"] == "0x116b888"
    assert target["region"] == "text"
    assert target["window"]["window_bytes"] == 0x100
    assert target["window"]["window_sha256"]
    assert target["window"]["reachable_decoded_words"] > 0
    assert target["window"]["bounded_window_not_function_extent"] is True
    assert target["target_is_callback_candidate_only"] is True
    assert target["callback_invocation_verified"] is False
    assert target["destructor_identity_verified"] is False
    assert target["function_extent_verified"] is False
    assert target["raw_aligned_word_census_only"] is True
    assert report["limits"]["registration_helper_identity_verified"] is False
    assert report["limits"]["registration_table_runtime_target_verified"] is False
    for key in (
        "callback_identity_verified", "destructor_identity_verified",
        "object_ownership_lifecycle_verified", "async_rollback_unbind_verified",
        "native_consumer_abi_verified", "archive_precedence_verified",
        "native_hook_added", "gameplay_verified", "full_moddingapi",
        "ready_for_gameplay_test", "emulator_tested",
    ):
        assert report["limits"][key] is False

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_registration_target.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_REGISTRATION_TARGET_PASS",
        target["address"],
        "reachable", target["window"]["reachable_decoded_words"],
        "direct_calls", len(target["window"]["direct_calls_not_walked"]),
        "NO_CALLBACK_NO_DESTRUCTOR_NO_ABI_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
