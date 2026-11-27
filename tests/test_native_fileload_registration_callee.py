"""Synthetic direct-callee regressions and exact original-main trace."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_registration_callee import analyze_callee, inspect


def expect_reject(fn, label):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(label + " was accepted")


def put_word(data, offset, word):
    struct.pack_into("<I", data, offset, word)


def encode_bl(site, target):
    delta = target - site
    if (delta & 3) or not -(1 << 27) <= delta < (1 << 27):
        raise ValueError("Synthetic BL target is out of range")
    return 0x94000000 | ((delta >> 2) & 0x03FFFFFF)


def synthetic_callee():
    data = bytearray(0x40)
    put_word(data, 0x00, encode_bl(0x00, 0x10))
    # The bounded callee reads through X0, performs an unresolved indirect call,
    # records a second direct call as a barrier, and returns.
    put_word(data, 0x10, 0xF9400001)  # ldr x1, [x0]
    put_word(data, 0x14, 0xD63F0020)  # blr x1
    put_word(data, 0x18, encode_bl(0x18, 0x28))
    put_word(data, 0x1C, 0xD65F03C0)  # ret
    put_word(data, 0x28, 0xD65F03C0)  # out-of-window callee body

    report = analyze_callee(bytes(data), 0x00, 0x10, 0x10)
    cfg = report["window"]
    summary = report["summary"]
    assert report["call_site"] == "0x0"
    assert report["target"] == "0x10"
    assert cfg["reachable_decoded_words"] == 4
    assert cfg["return_sites"] == ["0x1c"]
    assert cfg["unresolved_indirect_call_sites"] == ["0x14"]
    assert cfg["direct_calls_not_walked"] == [
        {"site": "0x18", "target": "0x28"}
    ]
    assert report["raw_aligned_text_B_BL_inbound_candidates"] == [
        {"site": "0x0", "branch_kind": "BL"}
    ]
    assert summary["x0_observations"]["read_sites"] == ["0x10"]
    assert summary["x0_observations"]["memory_base_sites"] == ["0x10"]
    assert summary["argument_register_access_counts"]["x0"]["reads"] == 1
    assert summary["direct_call_count"] == 1
    assert summary["unresolved_indirect_call_count"] == 1
    assert report["function_extent_verified"] is False

    # Reject wrong callsite target, B instead of BL, unaligned addresses,
    # empty windows, and windows that cross the available text boundary.
    expect_reject(
        lambda: analyze_callee(bytes(data), 0x00, 0x14, 0x10),
        "wrong direct-call target",
    )
    bad_branch = bytearray(data)
    put_word(bad_branch, 0x00, 0x14000004)  # b 0x10, not bl 0x10
    expect_reject(
        lambda: analyze_callee(bytes(bad_branch), 0x00, 0x10, 0x10),
        "tail branch in place of direct call",
    )
    expect_reject(
        lambda: analyze_callee(bytes(data), 0x02, 0x10, 0x10),
        "unaligned callsite",
    )
    expect_reject(
        lambda: analyze_callee(bytes(data), 0x00, 0x10, 0),
        "empty callee window",
    )
    expect_reject(
        lambda: analyze_callee(bytes(data), 0x00, 0x10, 0x40),
        "callee window past text end",
    )


def run(main, output):
    synthetic_callee()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["caller"]["load_site"] == "0x116b8a0"
    assert report["caller"]["direct_call_site"] == "0x116b8a4"
    assert report["caller"]["direct_call_target"] == "0x116b390"
    assert report["caller"]["load_memory_operand"] == {
        "base_register": "x8",
        "index_register": None,
        "displacement": 0x28,
        "access_size_bytes": 8,
        "width_source": "data_register_width",
        "direction": "read",
        "writeback": False,
    }
    callee = report["callee"]
    assert callee["target"] == "0x116b390"
    assert callee["window"]["window_bytes"] == 0x200
    assert callee["window"]["window_sha256"]
    assert callee["window"]["reachable_decoded_words"] > 0
    assert any(
        row["site"] == "0x116b8a4" and row["branch_kind"] == "BL"
        for row in callee["raw_aligned_text_B_BL_inbound_candidates"]
    )
    assert callee["function_extent_verified"] is False
    for key, value in report["limits"].items():
        assert value is False, (key, value)

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_registration_callee.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_REGISTRATION_CALLEE_PASS",
        callee["target"],
        "reachable", callee["window"]["reachable_decoded_words"],
        "direct_calls", callee["summary"]["direct_call_count"],
        "indirect_calls", callee["summary"]["unresolved_indirect_call_count"],
        "NO_CALLBACK_NO_DESTRUCTOR_NO_ABI_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
