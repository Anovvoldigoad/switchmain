"""Synthetic bounds tests plus exact original-main registration lifecycle trace."""
import argparse
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_registration_lifecycle import (
    decode_plt_thunk,
    inspect,
    read_c_string,
    require_direct_branch,
    trace_bounded_window,
)


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


def synthetic_regressions():
    text = bytearray(0x30)
    put_word(text, 0x10, 0xD503201F)
    put_word(text, 0x14, 0xD65F03C0)
    cfg = trace_bounded_window(bytes(text), 0x10, 0x10)
    assert cfg["reachable_decoded_words"] == 2
    assert cfg["return_sites"] == ["0x14"]
    assert cfg["bounded_window_not_function_extent"] is True
    expect_reject(lambda: trace_bounded_window(bytes(text), 0x12, 0x10),
                  "unaligned window")
    expect_reject(lambda: trace_bounded_window(bytes(text), 0x10, 0),
                  "empty window")
    expect_reject(lambda: trace_bounded_window(bytes(text), 0x10, 0x40),
                  "window beyond text")
    expect_reject(lambda: trace_bounded_window("not bytes", 0x10, 0x10),
                  "non-bytes text")

    # The original four-word AArch64 PLT pattern must be structurally complete.
    plt = struct.pack("<4I", 0xD0007270, 0xF9477E11,
                      0x913BE210, 0xD61F0220)
    decoded = decode_plt_thunk(plt, 0)
    assert decoded["got_slot"] > 0
    bad_plt = bytearray(plt)
    put_word(bad_plt, 12, 0xD65F03C0)
    expect_reject(lambda: decode_plt_thunk(bytes(bad_plt), 0),
                  "PLT without BR X17")
    expect_reject(lambda: decode_plt_thunk(plt, 2),
                  "unaligned PLT")

    branch_text = bytearray(0x20)
    put_word(branch_text, 0, encode_bl(0, 0x10))
    require_direct_branch(bytes(branch_text), 0, "BL", 0x10)
    expect_reject(lambda: require_direct_branch(
        bytes(branch_text), 0, "B", 0x10), "wrong branch kind")
    expect_reject(lambda: require_direct_branch(
        bytes(branch_text), 0, "BL", 0x14), "wrong branch target")

    raw = bytearray(b"\x00hello\x00tail")
    assert read_c_string(raw, 1, 1, 7) == b"hello"
    expect_reject(lambda: read_c_string(raw, 1, 1, 6),
                  "missing terminator before region end")
    expect_reject(lambda: read_c_string(raw, 8, 1, 7),
                  "string address outside region")
    expect_reject(lambda: read_c_string(raw, 1, 1, 7, 0),
                  "zero string budget")


def run(main, output):
    synthetic_regressions()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256

    helper = report["registration_helper"]
    assert helper["target"] == "0x290"
    assert helper["record_layout"]["stride_bytes"] == 24
    assert helper["record_layout"]["field_writes"] == [
        {"site": "0x304", "register": "x8", "offset": 0, "width": 8},
        {"site": "0x304", "register": "x1", "offset": 8, "width": 8},
        {"site": "0x308", "register": "x2", "offset": 0x10, "width": 8},
    ]
    assert helper["argument_candidates"]["field_0_code_pointer"]["target"] == "0x116b888"
    assert helper["argument_candidates"]["field_1_object_pointer"]["value"] == "0x43717e0"
    assert helper["argument_candidates"]["field_2_context_pointer"]["value"] == "0x1eb3000"

    cleanup = report["registered_code_pointer_target"]
    assert cleanup["address"] == "0x116b888"
    assert cleanup["window"]["window_bytes"] == 0x100
    assert cleanup["window"]["window_sha256"] == (
        "877fcd30e1fb00f75bf143dfb499419122edb72acf95677b73219ee7f0a809ec"
    )
    assert cleanup["cleanup_observations"]["slot_base"] == "0x4371800"
    assert cleanup["cleanup_observations"]["slot_count"] == 64
    assert cleanup["cleanup_observations"]["per_slot_direct_call"] == "0x116b390"
    assert cleanup["cleanup_observations"]["clear_covered_bytes"] == 0x200

    alternate = report["alternate_tail_import"]
    assert alternate["branch_site"] == "0x116d830"
    assert alternate["plt"] == "0x12f49b0"
    assert alternate["symbol"]["name"]
    assert alternate["relocation"]["type_name"] == "R_AARCH64_JUMP_SLOT"
    assert alternate["pointer_cell"]["address"] == "0x215d2e8"
    assert alternate["x2_value_at_tail_branch_verified"] is False

    error = report["index_error_path"]
    assert error["callsite"] == "0x116b864"
    assert error["target"] == "0x12155a0"
    assert error["literal_address"] == "0x1ae9d22"
    assert error["literal_bytes_hex"]
    assert error["target_window"]["window_bytes"] == 0x100

    for key, value in report["limits"].items():
        assert value is False, (key, value)

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_registration_lifecycle.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_REGISTRATION_LIFECYCLE_PASS",
        "helper_stride", helper["record_layout"]["stride_bytes"],
        "cleanup_slots", cleanup["cleanup_observations"]["slot_count"],
        "alternate_symbol", alternate["symbol"]["name"],
        "NO_DESTRUCTOR_NO_ABI_NO_UZUY_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
