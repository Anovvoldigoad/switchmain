"""Synthetic bounds/provenance regressions and pinned FileLoad table census."""
import argparse
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_table_access import (
    TABLE_END,
    TABLE_PAGE,
    TABLE_START,
    inspect,
    scan_address_page,
    scan_relocations_to_range,
    scan_direct_b_bl_inbound,
)


def expect_reject(fn, label):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(label + " was accepted")


def put_word(data, offset, word):
    struct.pack_into("<I", data, offset, word)


def encode_adrp(pc, register, page):
    delta = (page - (pc & ~0xFFF)) >> 12
    if not -(1 << 20) <= delta < (1 << 20):
        raise ValueError("Synthetic ADRP page delta is out of range")
    imm21 = delta & 0x1FFFFF
    return (0x90000000 | ((imm21 & 3) << 29)
            | (((imm21 >> 2) & 0x7FFFF) << 5) | register)


def encode_add(rd, rn, immediate):
    if not 0 <= immediate <= 0xFFF:
        raise ValueError("Synthetic ADD immediate is out of range")
    return 0x91000000 | (immediate << 10) | (rn << 5) | rd


def encode_str64(rt, rn, displacement):
    if displacement < 0 or displacement % 8 or displacement // 8 > 0xFFF:
        raise ValueError("Synthetic STR displacement is out of range")
    return 0xF9000000 | ((displacement // 8) << 10) | (rn << 5) | rt


def encode_ldr64(rt, rn, displacement):
    if displacement < 0 or displacement % 8 or displacement // 8 > 0xFFF:
        raise ValueError("Synthetic LDR displacement is out of range")
    return 0xF9400000 | ((displacement // 8) << 10) | (rn << 5) | rt


def encode_stp64(rt, rt2, rn, displacement):
    if displacement % 8 or not -64 * 8 <= displacement <= 63 * 8:
        raise ValueError("Synthetic STP displacement is out of range")
    imm7 = (displacement // 8) & 0x7F
    return 0xA9000000 | (imm7 << 15) | (rt2 << 10) | (rn << 5) | rt


def encode_mov64(rd, rm):
    return 0xAA0003E0 | (rm << 16) | rd


def encode_add_reg(rd, rn, rm):
    return 0x8B000000 | (rm << 16) | (rn << 5) | rd

def encode_add_uxtw_reg(rd, rn, rm, shift, option=2):
    if not 0 <= shift <= 4 or option not in (2, 6):
        raise ValueError("Synthetic extended ADD parameters are out of range")
    return (0x8B200000 | (rm << 16) | (option << 13)
            | (shift << 10) | (rn << 5) | rd)



def encode_branch(pc, target, link=False):
    delta = target - pc
    if delta % 4:
        raise ValueError("Synthetic branch target is not word aligned")
    immediate = delta // 4
    if not -(1 << 25) <= immediate < (1 << 25):
        raise ValueError("Synthetic branch target is out of range")
    return (0x94000000 if link else 0x14000000) | (immediate & 0x03FFFFFF)


def synthetic_direct_branch_scan():
    code = bytearray(0x40)
    put_word(code, 0x00, encode_branch(0x00, 0x20, link=True))
    put_word(code, 0x04, encode_branch(0x04, 0x20, link=False))
    put_word(code, 0x08, encode_branch(0x08, 0x30, link=True))
    put_word(code, 0x20, encode_branch(0x20, 0x00, link=False))
    rows = scan_direct_b_bl_inbound(bytes(code), 0x20)
    assert [(row["site"], row["kind"]) for row in rows] == [
        ("0x0", "BL"), ("0x4", "B")
    ]
    assert scan_direct_b_bl_inbound(bytes(code), 0x40) == []
    expect_reject(lambda: scan_direct_b_bl_inbound(bytes(code), 0x21),
                  "unaligned direct branch target")



def synthetic_page_scan():
    code = bytearray(0x80)
    put_word(code, 0x00, encode_adrp(0, 8, TABLE_PAGE))
    put_word(code, 0x04, encode_add(8, 8, TABLE_START - TABLE_PAGE))
    put_word(code, 0x08, encode_str64(0, 8, 0x10))
    put_word(code, 0x0C, encode_ldr64(1, 8, 0x18))
    put_word(code, 0x10, encode_stp64(0, 1, 8, 0x20))
    put_word(code, 0x14, encode_add(9, 8, TABLE_END - TABLE_START))
    put_word(code, 0x18, encode_str64(0, 9, 0))
    put_word(code, 0x1C, 0x14000001)  # B: bounded linear trace stops here.
    put_word(code, 0x20, encode_str64(0, 8, 0x28))
    report = scan_address_page(bytes(code), window_bytes=0x40)
    rows = {row["site"]: row for row in report["direct_accesses"]}
    assert report["page_reference_count"] == 1
    assert rows["0x8"]["direction"] == "write"
    assert rows["0x8"]["effective_address"] == "0x4371810"
    assert rows["0xc"]["direction"] == "read"
    assert rows["0xc"]["effective_address"] == "0x4371818"
    assert rows["0x10"]["direction"] == "write"
    assert rows["0x10"]["width_bytes"] == 16
    assert "0x18" not in rows  # Exact end boundary is excluded.
    assert "0x20" not in rows  # No linear fall-through after B.
    assert report["direct_access_census_complete"] is False

    clobbered = bytearray(0x30)
    put_word(clobbered, 0, encode_adrp(0, 8, TABLE_PAGE))
    put_word(clobbered, 4, encode_add(8, 8, TABLE_START - TABLE_PAGE))
    put_word(clobbered, 8, encode_mov64(8, 9))  # Unknown X9 replaces the address.
    put_word(clobbered, 12, encode_str64(0, 8, 0x10))
    assert scan_address_page(bytes(clobbered))["direct_accesses"] == []

    expect_reject(lambda: scan_address_page("not bytes"), "non-bytes text")
    expect_reject(lambda: scan_address_page(bytes(3)), "short text")
    expect_reject(lambda: scan_address_page(bytes(8), page=TABLE_PAGE + 1),
                  "unaligned page")
    expect_reject(lambda: scan_address_page(bytes(8), target_start=TABLE_START + 1),
                  "unaligned target start")
    expect_reject(lambda: scan_address_page(bytes(8), window_bytes=0),
                  "empty reference window")
    expect_reject(lambda: scan_address_page(bytes(8), target_end=TABLE_END + 0x1000),
                  "cross-page target range")


def synthetic_register_add_scan():
    code = bytearray(0x40)
    put_word(code, 0x00, encode_mov64(19, 31))  # X19 = XZR = 0 before ADRP.
    put_word(code, 0x04, encode_adrp(4, 20, TABLE_PAGE))
    put_word(code, 0x08, encode_add(20, 20, 0x7D8))
    put_word(code, 0x0C, encode_add_reg(8, 20, 19))
    put_word(code, 0x10, encode_ldr64(0, 8, 0x28))
    report = scan_address_page(bytes(code), window_bytes=0x40)
    assert len(report["direct_accesses"]) == 1
    row = report["direct_accesses"][0]
    assert row["site"] == "0x10"
    assert row["effective_address"] == hex(TABLE_START)
    kinds = [step["kind"] for step in row["origin_chain"]]
    assert "ADD_REGISTER" in kinds
    add = next(step for step in row["origin_chain"] if step["kind"] == "ADD_REGISTER")
    assert any(step["kind"] == "MOV_REGISTER" for step in add["right_chain"])

    unknown = bytearray(0x40)
    put_word(unknown, 0x04, encode_adrp(4, 20, TABLE_PAGE))
    put_word(unknown, 0x08, encode_add(20, 20, 0x7D8))
    put_word(unknown, 0x0C, encode_add_reg(8, 20, 19))  # X19 has no reaching value.
    put_word(unknown, 0x10, encode_ldr64(0, 8, 0x28))
    assert scan_address_page(bytes(unknown), window_bytes=0x40)["direct_accesses"] == []


def synthetic_dynamic_index_scan():
    code = bytearray(0x40)
    put_word(code, 0x00, encode_adrp(0, 8, TABLE_PAGE))
    put_word(code, 0x04, encode_add(8, 8, 0x7D8))
    put_word(code, 0x08, encode_add_uxtw_reg(8, 8, 1, 3))
    put_word(code, 0x0C, encode_ldr64(0, 8, 0x28))
    report = scan_address_page(bytes(code), window_bytes=0x30)
    assert len(report["indexed_access_candidates"]) == 1
    row = report["indexed_access_candidates"][0]
    assert row["site"] == "0xc"
    assert row["base_plus_displacement"] == hex(TABLE_START)
    assert row["index_register"] == "w1"
    assert row["index_scale"] == 8
    assert row["index_extension"] == "UXTW"
    assert row["direction"] == "read"
    assert row["effective_address_resolved"] is False

    code = bytearray(0x40)
    put_word(code, 0x00, encode_adrp(0, 8, TABLE_PAGE))
    put_word(code, 0x04, encode_add(8, 8, 0x7D8))
    put_word(code, 0x08, encode_add_uxtw_reg(9, 8, 1, 3))
    put_word(code, 0x0C, encode_mov64(10, 9))
    put_word(code, 0x10, encode_str64(0, 10, 0x28))
    report = scan_address_page(bytes(code), window_bytes=0x30)
    assert len(report["indexed_access_candidates"]) == 1
    row = report["indexed_access_candidates"][0]
    assert row["site"] == "0x10" and row["direction"] == "write"
    assert row["index_register"] == "w1"
    assert any(step["kind"] == "MOV_REGISTER" for step in row["origin_chain"])

    boundary = bytearray(0x40)
    put_word(boundary, 0x00, encode_adrp(0, 8, TABLE_PAGE))
    put_word(boundary, 0x04, encode_add(8, 8, TABLE_END - TABLE_PAGE - 0x28))
    put_word(boundary, 0x08, encode_add_uxtw_reg(8, 8, 1, 3))
    put_word(boundary, 0x0C, encode_ldr64(0, 8, 0x28))
    assert scan_address_page(bytes(boundary), window_bytes=0x30)["indexed_access_candidates"] == []

    unsupported = bytearray(0x40)
    put_word(unsupported, 0x00, encode_adrp(0, 8, TABLE_PAGE))
    put_word(unsupported, 0x04, encode_add(8, 8, 0x7D8))
    put_word(unsupported, 0x08, encode_add_uxtw_reg(8, 8, 1, 3, option=6))
    put_word(unsupported, 0x0C, encode_ldr64(0, 8, 0x28))
    assert scan_address_page(bytes(unsupported), window_bytes=0x30)["indexed_access_candidates"] == []


def synthetic_relocations():
    memory = bytearray(0x200)
    records = [
        (TABLE_START, 1027, 0x1234),
        (0x215D2B0, 1027, TABLE_START + 8),
        (TABLE_END, 1027, TABLE_END),
    ]
    for index, (destination, kind, addend) in enumerate(records):
        struct.pack_into("<QQq", memory, 0x40 + index * 24,
                         destination, kind, addend)
    report = scan_relocations_to_range(
        memory, {7: 0x40, 8: 72, 9: 24}, TABLE_START, TABLE_END
    )
    assert report["record_count_scanned"] == 3
    assert len(report["destinations_in_table_range"]) == 1
    assert len(report["addends_pointing_into_table_range"]) == 1
    assert report["destinations_in_table_range"][0]["destination"] == hex(TABLE_START)
    assert report["addends_pointing_into_table_range"][0]["addend"] == TABLE_START + 8
    assert scan_relocations_to_range(memory, {}, TABLE_START, TABLE_END)["record_count_scanned"] == 0

    expect_reject(lambda: scan_relocations_to_range(
        memory, {7: 0x40, 8: 72, 9: 16}, TABLE_START, TABLE_END
    ), "wrong RELA entry size")
    expect_reject(lambda: scan_relocations_to_range(
        memory, {7: 0x1F0, 8: 24, 9: 24}, TABLE_START, TABLE_END
    ), "RELA table out of bounds")
    expect_reject(lambda: scan_relocations_to_range(
        memory, {7: 0x40, 8: 24, 9: 24, 23: 0x40, 2: 24, 20: 7},
        TABLE_START, TABLE_END
    ), "overlapping RELA tables")


def run(main, output):
    synthetic_direct_branch_scan()
    synthetic_page_scan()
    synthetic_register_add_scan()
    synthetic_dynamic_index_scan()
    synthetic_relocations()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    table = report["table"]
    assert table["base"] == hex(TABLE_START)
    assert table["end_exclusive"] == hex(TABLE_END)
    assert table["slot_count"] == 64
    assert table["slot_stride_bytes"] == 8
    assert int(table["bss_start"], 16) <= TABLE_START
    assert int(table["bss_end"], 16) >= TABLE_END

    refs = {row["site"] for row in report["adrp_page_scan"]["page_references"]}
    assert {"0x116b894", "0x116b8bc", "0x116b940"} <= refs
    assert [row["first_slot_read"]["site"] for row in report["bounded_table_traversal_and_zeroing_candidates"]] == ["0x116b8a0", "0x116b924"]
    assert all(row["clear_covered_bytes"] == 512 and row["q0_zero_through_last_store_in_bounded_cfg"] for row in report["bounded_table_traversal_and_zeroing_candidates"])
    assert len(report["direct_reads"]) == 2
    assert len(report["direct_writes"]) == 32
    indexed = [row for row in report["indexed_access_candidates"]
               if row["site"] == "0x116b844"]
    assert len(indexed) == 1
    assert indexed[0]["base_plus_displacement"] == hex(TABLE_START)
    assert indexed[0]["index_register"] == "w1"
    assert indexed[0]["index_scale"] == 8
    assert indexed[0]["index_extension"] == "UXTW"
    assert indexed[0]["direction"] == "read"
    assert indexed[0]["effective_address_resolved"] is False
    assert report["direct_write_candidates_outside_two_zeroing_sequences"] == []
    helper_sites = {row["site"] for row in report["direct_b_bl_inbound"]["per_slot_helper_0x116b390"]}
    assert {"0x116b8a4", "0x116b928"} <= helper_sites
    assert any(call["site"] == "0x116b928" and call["target"] == "0x116b390" for call in report["bounded_table_traversal_and_zeroing_candidates"][1]["bounded_window"]["direct_calls_not_walked"])
    assert report["relocations"]["range_end_exclusive"] == hex(TABLE_END)
    for key, value in report["limits"].items():
        assert value is False, (key, value)

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_table_access.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_TABLE_ACCESS_CENSUS_PASS",
        "adrp_refs", report["adrp_page_scan"]["page_reference_count"],
        "direct_accesses", len(report["adrp_page_scan"]["direct_accesses"]),
        "indexed_accesses", len(report["indexed_access_candidates"]),
        "indexed_writers", len(report["indexed_write_candidates"]),
        "direct_writers_outside_two_zeroing_sequences",
        len(report["direct_write_candidates_outside_two_zeroing_sequences"]),
        "NO_PRODUCER_NO_ABI_NO_UZUY_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
