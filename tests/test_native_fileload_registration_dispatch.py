"""Synthetic target-window tests and exact pinned FileLoad dispatch-flow proof."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_registration_dispatch import inspect, trace_target


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


def synthetic_target():
    data = bytearray(0x40)
    put_word(data, 0x00, encode_bl(0x00, 0x10))
    put_word(data, 0x10, 0xF9400001)  # ldr x1, [x0]
    put_word(data, 0x14, 0xD65F03C0)  # ret
    report = trace_target(bytes(data), 0x10, 0x10)
    assert report["target"] == "0x10"
    assert report["window"]["reachable_decoded_words"] == 2
    assert report["window"]["return_sites"] == ["0x14"]
    assert report["summary"]["x0_observations"]["memory_base_sites"] == ["0x10"]
    assert report["raw_aligned_text_B_BL_inbound_candidates"] == [
        {"site": "0x0", "branch_kind": "BL"}
    ]
    assert report["function_extent_verified"] is False

    expect_reject(lambda: trace_target(bytes(data), 0x12, 0x10),
                  "unaligned target")
    expect_reject(lambda: trace_target(bytes(data), 0x10, 0),
                  "empty target window")
    expect_reject(lambda: trace_target(bytes(data), 0x10, 0x40),
                  "target window past text end")
    expect_reject(lambda: trace_target("not bytes", 0x10, 0x10),
                  "non-bytes text")


def run(main, output):
    synthetic_target()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["callee_target"] == "0x116b390"
    flow = report["dispatch_flow"]
    assert flow["entry_register_flow"] == {
        "source_register": "x0",
        "destination_register": "x19",
        "site": "0x116b398",
        "value_type_verified": False,
    }
    assert [(x["site"], x["target"]) for x in flow["direct_call_sequence"]] == [
        ("0x116b39c", "0x116b7b0"),
        ("0x116b3a4", "0x116d380"),
        ("0x116b3b0", "0x116b82c"),
    ]
    branch = flow["indirect_tail_branch"]
    assert branch["site"] == "0x116b3d0"
    assert branch["target_register"] == "x2"
    assert branch["x2_load_site"] == "0x116b3c4"
    assert branch["x2_memory_source"]["base_register"] == "x8"
    assert branch["x2_memory_source"]["displacement"] == 0x58
    assert branch["x8_load_site"] == "0x116b3bc"
    assert branch["x8_memory_source"]["base_register"] == "x0"
    assert branch["x8_memory_source"]["displacement"] == 0
    assert branch["x1_source_register"] == "x19"
    assert branch["branch_target_resolved"] is False
    assert flow["conditional_paths"]["alternate_branch_target"] == "0x116d820"
    assert flow["stack_observations"]["stack_frame_size_observed"] == 0x20

    traces = report["bounded_target_traces"]
    assert set(traces) == {"0x116b7b0", "0x116d380", "0x116b82c", "0x116d820"}
    for target, trace in traces.items():
        assert trace["target"] == target
        assert trace["window"]["window_bytes"] == 0x100
        assert trace["window"]["window_sha256"]
        assert trace["window"]["reachable_decoded_words"] > 0
        assert trace["function_extent_verified"] is False

    for key, value in report["limits"].items():
        assert value is False, (key, value)

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_registration_dispatch.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_REGISTRATION_DISPATCH_PASS",
        "targets", len(traces),
        "indirect_branch 0x116b3d0",
        "NO_CALLBACK_NO_DESTRUCTOR_NO_ABI_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
