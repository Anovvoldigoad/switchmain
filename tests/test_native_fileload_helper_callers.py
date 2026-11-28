"""Synthetic prelude regressions and exact pinned FileLoad helper caller census."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_helper_callers import (
    HELPER_TARGET,
    classify_callsite,
    inspect,
)


def expect_reject(fn, label):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(label + " was accepted")


def put_word(data, offset, word):
    struct.pack_into("<I", data, offset, word)


def encode_branch(site, target, link=False):
    delta = target - site
    if (delta & 3) or not -(1 << 27) <= delta < (1 << 27):
        raise ValueError("Synthetic branch target is out of range")
    opcode = 0x94000000 if link else 0x14000000
    return opcode | ((delta >> 2) & 0x03FFFFFF)


def encode_mov64(rd, rm):
    return 0xAA0003E0 | (rm << 16) | rd


def encode_ldr64(rt, rn, displacement):
    if displacement < 0 or displacement % 8 or displacement // 8 > 0xFFF:
        raise ValueError("Synthetic LDR displacement is out of range")
    return 0xF9400000 | ((displacement // 8) << 10) | (rn << 5) | rt


def synthetic_positive_and_memory_source():
    code = bytearray(0x80)
    put_word(code, 0x00, encode_mov64(0, 19))  # mov x0, x19
    put_word(code, 0x04, encode_mov64(1, 20))  # mov x1, x20
    put_word(code, 0x08, encode_ldr64(2, 3, 0x58))  # ldr x2, [x3, #0x58]
    put_word(code, 0x10, encode_branch(0x10, 0x40, link=True))
    row = classify_callsite(bytes(code), 0x10, 0x40, prelude_bytes=0x10)
    assert row["branch_kind"] == "BL"
    assert row["capstone_confirmed"] is True
    assert row["last_writes_are_not_proven_reaching_definitions"] is True
    defs = row["last_syntactic_writes_to_x0_x7"]
    assert defs["x0"]["pc"] == "0x0"
    assert defs["x0"]["mnemonic"] == "mov"
    assert defs["x1"]["pc"] == "0x4"
    assert defs["x2"]["pc"] == "0x8"
    memory = defs["x2"]["memory_operands"]
    assert memory == [{
        "operand_index": 1,
        "base_register": "x3",
        "index_register": None,
        "displacement": 0x58,
        "width_bytes": 8,
        "width_source": "data_register_width",
        "direction": "read",
        "writeback": False,
    }]
    assert row["path_continuity_proven"] is False
    assert row["function_extent_verified"] is False


def synthetic_tail_branch_and_control_flow_barrier():
    code = bytearray(0x80)
    put_word(code, 0x00, encode_branch(0x00, 0x60, link=True))
    put_word(code, 0x04, encode_mov64(0, 19))
    put_word(code, 0x08, encode_branch(0x08, 0x40, link=False))
    row = classify_callsite(bytes(code), 0x08, 0x40, prelude_bytes=0x08)
    assert row["branch_kind"] == "B"
    assert row["control_flow_sites"] == [{
        "site": "0x0",
        "mnemonic": "bl",
        "operands": "#0x60",
    }]
    assert row["last_syntactic_writes_to_x0_x7"]["x0"]["pc"] == "0x4"
    assert row["path_continuity_proven"] is False


def synthetic_last_write_clobber_and_window_boundary():
    code = bytearray(0x80)
    put_word(code, 0x00, encode_mov64(0, 19))
    put_word(code, 0x04, encode_mov64(0, 9))
    put_word(code, 0x08, encode_branch(0x08, 0x40, link=True))
    row = classify_callsite(bytes(code), 0x08, 0x40, prelude_bytes=0x08)
    assert row["last_syntactic_writes_to_x0_x7"]["x0"]["pc"] == "0x4"
    assert row["last_syntactic_writes_to_x0_x7"]["x0"]["read_registers"] == ["x9"]

    boundary = bytearray(0x40)
    put_word(boundary, 0x00, encode_branch(0x00, 0x20, link=True))
    row = classify_callsite(bytes(boundary), 0x00, 0x20, prelude_bytes=0x40)
    assert row["prelude_start"] == "0x0"
    assert row["prelude_instruction_count"] == 0
    assert all(value is None for value in row["last_syntactic_writes_to_x0_x7"].values())


def synthetic_rejections():
    code = bytearray(0x40)
    put_word(code, 0x00, encode_mov64(0, 19))
    put_word(code, 0x04, encode_branch(0x04, 0x20, link=True))
    expect_reject(lambda: classify_callsite("not bytes", 0x04, 0x20),
                  "non-bytes text")
    expect_reject(lambda: classify_callsite(bytes(code), 0x05, 0x20),
                  "unaligned callsite")
    expect_reject(lambda: classify_callsite(bytes(code), 0x04, 0x21),
                  "unaligned target")
    expect_reject(lambda: classify_callsite(bytes(code), 0x04, 0x24),
                  "wrong direct target")
    expect_reject(lambda: classify_callsite(bytes(code), 0x04, 0x20, -4),
                  "negative prelude")
    expect_reject(lambda: classify_callsite(bytes(code), 0x04, 0x20, 6),
                  "unaligned prelude")
    expect_reject(lambda: classify_callsite(bytes(code), 0x04, 0x20, 0x104),
                  "oversized prelude")
    expect_reject(lambda: classify_callsite(bytes(code), 0x40, 0x20),
                  "branch site outside text")


def run(main, output):
    synthetic_positive_and_memory_source()
    synthetic_tail_branch_and_control_flow_barrier()
    synthetic_last_write_clobber_and_window_boundary()
    synthetic_rejections()

    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["helper_target"] == hex(HELPER_TARGET)
    assert report["raw_aligned_direct_b_bl_inbound_count"] == 114, (
        "stale 101-count checkpoint; pinned raw census observed "
        + str(report["raw_aligned_direct_b_bl_inbound_count"])
    )
    assert report["raw_branch_kind_counts"] == {"BL": 111, "B": 3}
    assert report["prelude_bytes_per_caller"] == 0x40
    assert report["capstone_confirmed_direct_branch_count"] + len(
        report["capstone_unconfirmed_raw_candidates"]
    ) == 101
    assert report["known_table_path_helper_calls"] == [
        {
            "call_site": "0x116b8a4",
            "call_target": "0x116b390",
            "load_site": "0x116b8a0",
            "load_word_le": report["known_table_path_helper_calls"][0]["load_word_le"],
            "load_mnemonic": "ldr",
            "load_operands": "x0, [x8, #0x28]",
            "memory_operand": {
                "operand_index": 1,
                "base_register": "x8",
                "index_register": None,
                "displacement": 0x28,
                "width_bytes": 8,
                "width_source": "data_register_width",
                "direction": "read",
                "writeback": False,
            },
            "value_type_verified": False,
            "function_extent_verified": False,
        },
        {
            "call_site": "0x116b928",
            "call_target": "0x116b390",
            "load_site": "0x116b924",
            "load_word_le": report["known_table_path_helper_calls"][1]["load_word_le"],
            "load_mnemonic": "ldr",
            "load_operands": "x0, [x8, #0x28]",
            "memory_operand": {
                "operand_index": 1,
                "base_register": "x8",
                "index_register": None,
                "displacement": 0x28,
                "width_bytes": 8,
                "width_source": "data_register_width",
                "direction": "read",
                "writeback": False,
            },
            "value_type_verified": False,
            "function_extent_verified": False,
        },
    ]
    assert sum(group["count"] for group in report["signature_clusters"]) == (
        report["capstone_confirmed_direct_branch_count"]
    )
    assert report["scope"]["prelude_last_writes_are_syntactic_not_reaching_definitions"]
    assert report["scope"]["indirect_branches_and_conditional_inbound_edges_not_scanned"]
    for key, value in report["limits"].items():
        assert value is False, (key, value)

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_helper_callers.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_HELPER_CALLER_CENSUS_PASS",
        "raw_candidates", report["raw_aligned_direct_b_bl_inbound_count"],
        "capstone_confirmed", report["capstone_confirmed_direct_branch_count"],
        "clusters", len(report["signature_clusters"]),
        "NO_ABI_NO_OWNER_NO_UZUY_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
