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
    if delta & 0xFFF:
        raise ValueError("Synthetic ADRP target is not page aligned")
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
    synthetic_page_scan()
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
    assert {"0x116b894", "0x116b8bc"} <= refs
    assert report["first_slot_load"]["site"] == "0x116b8a0"
    assert report["first_slot_load"]["effective_address"] == hex(TABLE_START)
    assert len(report["cleanup_clear_writes"]) == 16
    assert [row["site"] for row in report["cleanup_clear_writes"]] == [
        hex(site) for site in range(0x116B8C4, 0x116B904, 4)
    ]
    assert all(row["width_bytes"] == 32
               for row in report["cleanup_clear_writes"])
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
        "direct_writers_outside_cleanup",
        len(report["direct_write_candidates_outside_cleanup"]),
        "NO_PRODUCER_NO_ABI_NO_UZUY_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
