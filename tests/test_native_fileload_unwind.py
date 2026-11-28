"""Synthetic DWARF CFI regressions and pinned Switch main unwind census."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_unwind import (
    _header,
    _scan_linear,
    discover_metadata,
    inspect,
    map_callers_to_fdes,
)


def put_u32(data, offset, value):
    struct.pack_into("<I", data, offset, value & 0xffffffff)


def put_s32(data, offset, value):
    struct.pack_into("<i", data, offset, value)


def fixture(fde_count=2, with_header=True, bad_cie=False, bad_range=False):
    text_va = 0
    text = bytearray(0x3000)
    ro_va = 0x4000
    ro = bytearray(0x1000)
    cie_offset = 0x40
    body = (
        struct.pack("<I", 0)
        + b"\x01zR\x00"
        + b"\x01\x78\x1e\x01\x1b"
        + b"\x00\x00\x00"
    )
    assert len(body) == 16
    put_u32(ro, cie_offset, len(body))
    ro[cie_offset + 4:cie_offset + 4 + len(body)] = body

    fde_offsets = []
    starts = []
    next_offset = cie_offset + 4 + len(body)
    for index in range(fde_count):
        fde_offset = next_offset
        fde_offsets.append(fde_offset)
        start = 0x1000 + index * 0x100
        starts.append(start)
        cie_field = fde_offset + 4
        cie_pointer = cie_field - (cie_offset + (4 if bad_cie else 0))
        initial_field = fde_offset + 8
        initial_delta = start - (ro_va + initial_field)
        address_range = 0x30
        if bad_range and index == 0:
            address_range = 0x4000
        fde_body = (
            struct.pack("<I", cie_pointer)
            + struct.pack("<i", initial_delta)
            + struct.pack("<i", address_range)
            + b"\x00\x00\x00\x00"
        )
        assert len(fde_body) == 16
        put_u32(ro, fde_offset, len(fde_body))
        ro[fde_offset + 4:fde_offset + 4 + len(fde_body)] = fde_body
        next_offset = fde_offset + 4 + len(fde_body)

    if with_header:
        ro[0:4] = b"\x01\x1b\x03\x3b"
        put_s32(ro, 4, (ro_va + cie_offset) - (ro_va + 4))
        put_u32(ro, 8, fde_count)
        for index, (start, fde_offset) in enumerate(zip(starts, fde_offsets)):
            table_at = 12 + index * 8
            put_s32(ro, table_at, start - ro_va)
            put_s32(ro, table_at + 4, fde_offset)
    return text, ro, text_va, ro_va, starts, fde_offsets


def expect_reject(fn, label):
    try:
        fn()
    except (ValueError, IndexError, struct.error):
        return
    raise AssertionError(label + " was accepted")


def synthetic_header_positive_and_boundaries():
    text, ro, text_va, ro_va, starts, fde_offsets = fixture()
    report = _header(ro, ro_va, text_va, len(text), 0)
    assert report["source"] == "GNU_EH_FRAME_HDR"
    assert report["fde_count"] == 2
    assert [row["start"] for row in report["fdes"]] == starts
    assert [row["fde_offset"] for row in report["fdes"]] == fde_offsets
    assert report["pointer_encodings"] == {
        "eh_frame_ptr": "0x1b", "fde_count": "0x3", "table": "0x3b"
    }
    discovered = discover_metadata([
        (text_va, text, b""),
        (ro_va, ro, b""),
        (0x8000, bytes(0x100), b""),
    ])
    assert discovered["status"] == "GNU_EH_FRAME_HDR_VALIDATED"
    assert len(discovered["fde_records"]) == 2
    callers = [
        {"site": hex(starts[0]), "branch_kind": "BL"},
        {"site": hex(starts[0] + 0x2f), "branch_kind": "BL"},
        {"site": hex(starts[0] + 0x30), "branch_kind": "BL"},
        {"site": hex(starts[1]), "branch_kind": "B"},
    ]
    mappings, ranges = map_callers_to_fdes(callers, report["fdes"], text)
    assert [row["mapping_status"] for row in mappings] == [
        "UNIQUE_FDE_COVERAGE", "UNIQUE_FDE_COVERAGE", "UNMAPPED",
        "UNIQUE_FDE_COVERAGE"
    ]
    assert len(ranges) == 2
    assert all(row["range_is_unwind_coverage_not_function_identity"] for row in ranges)


def synthetic_linear_fde_sequence():
    text, ro, text_va, ro_va, starts, _ = fixture(
        fde_count=MIN_FDES, with_header=False
    )
    candidates, diag = _scan_linear(ro, ro_va, text_va, len(text))
    assert diag["cie_candidates_scanned"] >= 1
    assert len(candidates) == 1
    assert candidates[0]["fde_count"] == MIN_FDES
    assert [row["start"] for row in candidates[0]["fdes"]] == starts


def synthetic_rejections():
    text, ro, text_va, ro_va, _starts, _fds = fixture()
    invalid_version = bytearray(ro)
    invalid_version[0] = 2
    expect_reject(lambda: _header(invalid_version, ro_va, text_va, len(text), 0),
                  "invalid header version")

    unsupported_encoding = bytearray(ro)
    unsupported_encoding[1] = 0x4b
    expect_reject(lambda: _header(unsupported_encoding, ro_va, text_va, len(text), 0),
                  "unsupported header encoding")

    unsorted = bytearray(ro)
    first = bytes(unsorted[12:20])
    second = bytes(unsorted[20:28])
    unsorted[12:20] = second
    unsorted[20:28] = first
    expect_reject(lambda: _header(unsorted, ro_va, text_va, len(text), 0),
                  "unsorted table")

    bad_cie_text, bad_cie_ro, bad_cie_va, bad_ro_va, *_ = fixture(bad_cie=True)
    expect_reject(lambda: _header(
        bad_cie_ro, bad_ro_va, bad_cie_va, len(bad_cie_text), 0
    ), "invalid CIE back-reference")

    bad_range_text, bad_range_ro, bad_range_va, bad_range_ro_va, *_ = fixture(
        bad_range=True
    )
    expect_reject(lambda: _header(
        bad_range_ro, bad_range_ro_va, bad_range_va, len(bad_range_text), 0
    ), "FDE range outside executable text")

    truncated = bytearray(ro[:24])
    expect_reject(lambda: _header(truncated, ro_va, text_va, len(text), 0),
                  "truncated search table")

    oversized = bytearray(ro)
    put_u32(oversized, 8, 0xffffffff)
    expect_reject(lambda: _header(oversized, ro_va, text_va, len(text), 0),
                  "oversized FDE count")


MIN_FDES = 8


def synthetic_ambiguous_mapping_and_absent_metadata():
    overlapping = [
        {
            "start": 0x100, "end": 0x200, "range": 0x100,
            "fde_offset": 0x40, "cie_offset": 0x20,
            "fde_sha256": "a" * 64,
        },
        {
            "start": 0x180, "end": 0x280, "range": 0x100,
            "fde_offset": 0x80, "cie_offset": 0x20,
            "fde_sha256": "b" * 64,
        },
    ]
    mappings, ranges = map_callers_to_fdes(
        [{"site": "0x190", "branch_kind": "BL"}], overlapping, bytes(0x300)
    )
    assert mappings[0]["mapping_status"] == "AMBIGUOUS"
    assert mappings[0]["matching_fde_count"] == 2
    assert ranges == []

    absent = discover_metadata([
        (0, bytes(0x300), b""),
        (0x4000, bytes(0x200), b""),
        (0x8000, bytes(0x100), b""),
    ])
    assert absent["status"] == "NO_RELIABLE_CFI_METADATA_FOUND"
    assert absent["fde_records"] == []


def run(main, output):
    synthetic_header_positive_and_boundaries()
    synthetic_linear_fde_sequence()
    synthetic_rejections()
    synthetic_ambiguous_mapping_and_absent_metadata()

    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["original_main_bytes"] == 27701509
    assert report["caller_census_dependency"] == {
        "target": "0x116b390",
        "raw_candidates": 114,
        "capstone_confirmed": 114,
        "unconfirmed": 0,
    }
    assert report["caller_mapping"]["total"] == 114
    assert sum(report["caller_mapping"]["counts"].values()) == 114
    assert [row["call_site"] for row in report["table_path_callers"]] == [
        "0x116b8a4", "0x116b928"
    ]
    for key, value in report["limits"].items():
        assert value is False or (
            key == "fde_range_is_exact_cfi_coverage_only" and value is True
        )
    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_unwind.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_UNWIND_SCAN_PASS",
        report["metadata"]["status"],
        "fde_records", report["metadata"]["fde_records_validated"],
        "mapped", report["caller_mapping"]["counts"]["unique_fde_coverage"],
        "unmapped", report["caller_mapping"]["counts"]["unmapped"],
        "ambiguous", report["caller_mapping"]["counts"]["ambiguous"],
        "NO_FUNCTION_IDENTITY_NO_ABI_NO_OWNER_NO_UZUY",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
