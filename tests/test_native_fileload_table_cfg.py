"""Synthetic regressions and pinned-main FileLoad table CFG evidence."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_table_access import TABLE_END, TABLE_PAGE, TABLE_START
from portlib.native_fileload_table_cfg import (
    collect_static_pointer_cells,
    inspect,
    scan_address_pages_cfg,
    _summarize_counted_slot_loop,
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


def encode_ldr64(rt, rn, displacement):
    if displacement < 0 or displacement % 8 or displacement // 8 > 0xFFF:
        raise ValueError("Synthetic LDR displacement is out of range")
    return 0xF9400000 | ((displacement // 8) << 10) | (rn << 5) | rt


def encode_str64(rt, rn, displacement):
    if displacement < 0 or displacement % 8 or displacement // 8 > 0xFFF:
        raise ValueError("Synthetic STR displacement is out of range")
    return 0xF9000000 | ((displacement // 8) << 10) | (rn << 5) | rt


def encode_branch(pc, target, link=False):
    delta = target - pc
    if delta % 4:
        raise ValueError("Synthetic branch target is not aligned")
    immediate = delta // 4
    if not -(1 << 25) <= immediate < (1 << 25):
        raise ValueError("Synthetic branch target is out of range")
    return (0x94000000 if link else 0x14000000) | (immediate & 0x03FFFFFF)


def encode_b_cond(pc, target, condition=0):
    delta = target - pc
    if delta % 4 or not 0 <= condition <= 15:
        raise ValueError("Synthetic conditional branch parameters are invalid")
    immediate = delta // 4
    if not -(1 << 18) <= immediate < (1 << 18):
        raise ValueError("Synthetic conditional branch target is out of range")
    return 0x54000000 | ((immediate & 0x7FFFF) << 5) | condition


def synthetic_branch_path_write():
    code = bytearray(0x80)
    put_word(code, 0x00, encode_adrp(0x00, 8, TABLE_PAGE))
    put_word(code, 0x04, encode_add(8, 8, TABLE_START - TABLE_PAGE))
    put_word(code, 0x08, encode_b_cond(0x08, 0x20))
    put_word(code, 0x0C, encode_branch(0x0C, 0x70))
    put_word(code, 0x20, encode_str64(0, 8, 0x10))
    report = scan_address_pages_cfg(bytes(code), {TABLE_PAGE}, {}, window_bytes=0x40)
    writes = [row for row in report["direct_accesses"]
              if row["site"] == "0x20" and row["direction"] == "write"]
    assert len(writes) == 1
    assert writes[0]["effective_address"] == hex(TABLE_START + 0x10)
    assert writes[0]["branch_path_witnesses"] == [["0x8"]]
    assert report["branch_path_table_writes"] == writes
    assert report["bounded_in_window_cfg_complete"] is True

    no_branch_target = bytearray(0x80)
    put_word(no_branch_target, 0x00, encode_adrp(0x00, 8, TABLE_PAGE))
    put_word(no_branch_target, 0x04, encode_add(8, 8, TABLE_START - TABLE_PAGE))
    put_word(no_branch_target, 0x08, encode_b_cond(0x08, 0x80))
    report = scan_address_pages_cfg(
        bytes(no_branch_target), {TABLE_PAGE}, {}, window_bytes=0x40
    )
    assert report["direct_accesses"] == []
    assert any(row["target"] == "0x80" for row in report["out_of_window_edges"])


def synthetic_equivalent_branch_histories_merge():
    code = bytearray(0x60)
    put_word(code, 0x00, encode_adrp(0x00, 8, TABLE_PAGE))
    put_word(code, 0x04, encode_add(8, 8, TABLE_START - TABLE_PAGE))
    put_word(code, 0x08, encode_b_cond(0x08, 0x20))
    put_word(code, 0x0C, 0xD503201F)  # NOP on the fallthrough path.
    put_word(code, 0x10, encode_branch(0x10, 0x20))
    put_word(code, 0x20, encode_str64(0, 8, 0x10))
    report = scan_address_pages_cfg(bytes(code), {TABLE_PAGE}, {}, window_bytes=0x40)
    writes = [row for row in report["direct_accesses"]
              if row["site"] == "0x20" and row["direction"] == "write"]
    assert len(writes) == 1
    assert writes[0]["effective_address"] == hex(TABLE_START + 0x10)
    assert len(writes[0]["branch_path_witnesses"]) == 1
    assert writes[0]["branch_path_witnesses"][0] in (
        ["0x8"], ["0x10"]
    )
    assert report["equivalent_branch_histories_merged"] >= 1
    assert report["branch_path_witnesses_exhaustive"] is False
    assert report["bounded_in_window_cfg_complete"] is True


def synthetic_distinct_register_states_do_not_merge():
    code = bytearray(0x60)
    put_word(code, 0x00, encode_adrp(0x00, 8, TABLE_PAGE))
    put_word(code, 0x04, encode_add(8, 8, TABLE_START - TABLE_PAGE))
    put_word(code, 0x08, encode_b_cond(0x08, 0x1C))
    put_word(code, 0x0C, encode_add(8, 8, 0x10))
    put_word(code, 0x10, encode_branch(0x10, 0x28))
    put_word(code, 0x1C, encode_add(8, 8, 0x20))
    put_word(code, 0x20, encode_branch(0x20, 0x28))
    put_word(code, 0x28, encode_str64(0, 8, 0))
    report = scan_address_pages_cfg(bytes(code), {TABLE_PAGE}, {}, window_bytes=0x40)
    writes = [row for row in report["direct_accesses"]
              if row["site"] == "0x28" and row["direction"] == "write"]
    assert {row["effective_address"] for row in writes} == {
        hex(TABLE_START + 0x10), hex(TABLE_START + 0x20)
    }
    assert len(writes) == 2
    assert report["equivalent_branch_histories_merged"] == 0
    assert report["branch_path_witnesses_exhaustive"] is True
    assert report["bounded_in_window_cfg_complete"] is True


def synthetic_call_barrier():
    code = bytearray(0x40)
    put_word(code, 0x00, encode_adrp(0x00, 8, TABLE_PAGE))
    put_word(code, 0x04, encode_add(8, 8, TABLE_START - TABLE_PAGE))
    put_word(code, 0x08, encode_branch(0x08, 0x70, link=True))
    put_word(code, 0x0C, encode_str64(0, 8, 0x10))
    report = scan_address_pages_cfg(bytes(code), {TABLE_PAGE}, {}, window_bytes=0x30)
    assert report["direct_accesses"] == []
    assert report["call_barriers"] == [
        {"site": "0x8", "kind": "call", "target": "0x70"}
    ]


def synthetic_static_pointer_cells():
    memory = bytearray(0x6000)
    text_data = bytearray(0x100)
    struct.pack_into("<Q", text_data, 0x80, TABLE_PAGE + 0x7D8)
    memory[0:0x100] = text_data
    data = bytearray(0x100)
    struct.pack_into("<Q", data, 0x80, TABLE_PAGE + 0x7D8)
    struct.pack_into("<Q", memory, 0x200, 0x5090)
    struct.pack_into("<Q", memory, 0x208, 1027)
    struct.pack_into("<q", memory, 0x210, TABLE_PAGE + 0x800)
    struct.pack_into("<Q", memory, 0x218, 0x50A0)
    struct.pack_into("<Q", memory, 0x220, 1027)
    struct.pack_into("<q", memory, 0x228, TABLE_PAGE + 0x1000)
    memory[0x5000:0x5100] = data
    cells = collect_static_pointer_cells(
        [(0x0000, bytes(text_data), 0x0000), (0x5000, bytes(data), 0x5000)],
        memory,
        {7: 0x200, 8: 48, 9: 24},
    )
    assert 0x0080 not in cells  # Executable text words are not pointer-cell candidates.
    assert cells[0x5080] == [
        {"value": TABLE_PAGE + 0x7D8, "source": "FILE_BACKED_LITERAL"}
    ]
    assert cells[0x5090] == [
        {"value": TABLE_PAGE + 0x800, "source": "DT_RELA:R_AARCH64_RELATIVE"}
    ]
    assert 0x50A0 not in cells  # Exact target-page end is excluded.
    assert 0x5200 not in cells  # BSS bytes are not treated as file-backed literals.

    expect_reject(lambda: collect_static_pointer_cells(
        [(0x0000, bytes(text_data), 0x0000), (0x5000, bytes(data), 0x5000)], memory, {7: 0x200, 8: 48, 9: 16}
    ), "invalid RELA entry size")
    expect_reject(lambda: collect_static_pointer_cells(
        [(0x0000, bytes(text_data), 0x0000), (0x5000, bytes(data), 0x5000)], memory, {7: 0x5FF0, 8: 24, 9: 24}
    ), "out-of-bounds RELA table")
    expect_reject(lambda: collect_static_pointer_cells(
        [(0x0000, bytes(text_data), 0x0000), (0x5000, bytes(data), 0x5000)], memory, {7: 0x200}
    ), "incomplete RELA tag pair")


def synthetic_memory_loaded_alias():
    code = bytearray(0x40)
    pointer_page = 0x5000
    put_word(code, 0x00, encode_adrp(0x00, 9, pointer_page))
    put_word(code, 0x04, encode_add(9, 9, 0x80))
    put_word(code, 0x08, encode_ldr64(8, 9, 0))
    put_word(code, 0x0C, encode_str64(0, 8, 0x10))
    cells = {
        0x5080: [{
            "value": TABLE_START,
            "source": "SYNTHETIC_R_AARCH64_RELATIVE",
        }]
    }
    report = scan_address_pages_cfg(
        bytes(code), {pointer_page}, cells, window_bytes=0x30
    )
    assert len(report["memory_loaded_aliases"]) == 1
    alias = report["memory_loaded_aliases"][0]
    assert alias["cell_address"] == "0x5080"
    assert alias["loaded_value"] == hex(TABLE_START)
    writes = [row for row in report["direct_accesses"]
              if row["site"] == "0xc" and row["direction"] == "write"]
    assert len(writes) == 1
    assert writes[0]["effective_address"] == hex(TABLE_START + 0x10)
    assert any(step["kind"] == "STATIC_POINTER_LOAD"
               for step in writes[0]["origin_candidates"][0]["origin_chain"])

    absent = scan_address_pages_cfg(
        bytes(code), {pointer_page}, {}, window_bytes=0x30
    )
    assert absent["direct_accesses"] == []

    ambiguous = scan_address_pages_cfg(
        bytes(code), {pointer_page}, {
            0x5080: [
                {"value": TABLE_START, "source": "A"},
                {"value": TABLE_START + 8, "source": "B"},
            ]
        }, window_bytes=0x30
    )
    assert ambiguous["direct_accesses"] == []
    assert len(ambiguous["ambiguous_pointer_loads"]) == 1

    end_pointer = scan_address_pages_cfg(
        bytes(code), {pointer_page}, {
            0x5080: [{"value": TABLE_PAGE + 0x1000, "source": "END"}]
        }, window_bytes=0x30
    )
    assert end_pointer["direct_accesses"] == []


def synthetic_counted_slot_loop():
    site = 0x116BF54
    base_address = site - 8
    data = bytearray(0x40)
    words = [
        (-8, "f4031faa"),  # mov x20, xzr
        (-4, "1f2003d5"),  # nop; no counter write between init and ADRP
        (0, "359001d0"),   # adrp x21, #0x4371000
        (4, "b5621f91"),   # add x21, x21, #0x7d8
        (8, "04000014"),   # b site+0x18
        (12, "94220091"),  # add x20, x20, #8
        (16, "9f0208f1"),  # cmp x20, #0x200
        (20, "20010054"),  # b.eq site+0x38
        (24, "a802148b"),  # add x8, x21, x20
        (28, "001540f9"),  # ldr x0, [x8, #0x28]
        (32, "60ffffb4"),  # cbz x0, update
        (36, "080040f9"),  # ldr x8, [x0]
        (40, "083140f9"),  # ldr x8, [x8, #0x60]
        (44, "00013fd6"),  # blr x8
        (48, "1300138b"),  # add x19, x0, x19
        (52, "f6ffff17"),  # b update
    ]

    def build(dispatch_word="083140f9"):
        result = bytearray(data)
        for offset, word in words:
            if offset == 40:
                word = dispatch_word
            result[offset - (base_address - site):offset - (base_address - site) + 4] = bytes.fromhex(word)
        return result

    positive = build()
    summary = _summarize_counted_slot_loop(
        bytes(positive), site, base_address
    )
    assert summary["state"] == (
        "PROVEN_STATIC_LOOP_STRUCTURE_CONDITIONAL_ON_X20_PRESERVATION"
    )
    assert summary["counter"]["iteration_count_if_preserved"] == 64
    assert summary["table_read"]["base"] == hex(TABLE_START)
    assert summary["table_read"]["end_exclusive_if_counter_preserved"] == hex(TABLE_END)
    assert summary["indirect_dispatch"]["callee_preserves_x20_verified"] is False

    second_dispatch = build("083540f9")
    assert _summarize_counted_slot_loop(
        bytes(second_dispatch), site, base_address
    )["indirect_dispatch"]["target_load_offset"] == 0x68

    bad_stride = bytearray(positive)
    bad_stride[20:24] = struct.pack("<I", encode_add(20, 20, 16))
    expect_reject(lambda: _summarize_counted_slot_loop(
        bytes(bad_stride), site, base_address
    ), "non-eight-byte loop stride")

    bad_limit = bytearray(positive)
    bad_limit[24:28] = bytes(4)
    expect_reject(lambda: _summarize_counted_slot_loop(
        bytes(bad_limit), site, base_address
    ), "non-table loop bound")

    bad_read = bytearray(positive)
    bad_read[36:40] = struct.pack("<I", encode_str64(0, 8, 0x28))
    expect_reject(lambda: _summarize_counted_slot_loop(
        bytes(bad_read), site, base_address
    ), "table write instead of read")

    bad_dispatch = bytearray(positive)
    bad_dispatch[48:52] = bytes.fromhex("083940f9")
    expect_reject(lambda: _summarize_counted_slot_loop(
        bytes(bad_dispatch), site, base_address
    ), "unrecognized dispatch offset")

    bad_init = bytearray(positive)
    bad_init[0:4] = bytes(4)
    expect_reject(lambda: _summarize_counted_slot_loop(
        bytes(bad_init), site, base_address
    ), "unknown initial counter value")

    bad_pre_init = bytearray(positive)
    bad_pre_init[4:8] = bytes.fromhex("f40313aa")
    expect_reject(lambda: _summarize_counted_slot_loop(
        bytes(bad_pre_init), site, base_address
    ), "counter overwritten after initialization")


def synthetic_limits():
    code = bytearray(0x40)
    put_word(code, 0x00, encode_adrp(0x00, 8, TABLE_PAGE))
    put_word(code, 0x04, encode_add(8, 8, TABLE_START - TABLE_PAGE))
    put_word(code, 0x08, encode_b_cond(0x08, 0x20))
    put_word(code, 0x0C, encode_str64(0, 8, 0x10))
    put_word(code, 0x20, encode_str64(0, 8, 0x18))
    limited = scan_address_pages_cfg(
        bytes(code), {TABLE_PAGE}, {}, window_bytes=0x30, max_states=1
    )
    assert limited["state_budget_exceeded"] is True
    assert limited["bounded_in_window_cfg_complete"] is False

    budget_code = bytearray(0x40)
    put_word(budget_code, 0x00, encode_adrp(0x00, 8, TABLE_PAGE))
    put_word(budget_code, 0x04, encode_adrp(0x04, 9, 0x5000))
    put_word(budget_code, 0x08, encode_adrp(0x08, 10, 0x5000))
    budgeted = scan_address_pages_cfg(
        bytes(budget_code), {TABLE_PAGE, 0x5000}, {},
        window_bytes=0x30, max_references=1
    )
    assert budgeted["target_page_cfg_complete"] is True
    assert budgeted["reference_budget_exceeded"] is True
    assert budgeted["pages_skipped"] == [{
        "page": "0x5000",
        "candidate_reference_count": 2,
        "remaining_reference_budget": 0,
        "reason": "reference_budget_exceeded",
    }]

    expect_reject(lambda: scan_address_pages_cfg(bytes(code), set(), {}),
                  "empty page set")
    expect_reject(lambda: scan_address_pages_cfg(bytes(code), {TABLE_PAGE + 1}, {}),
                  "unaligned page")
    expect_reject(lambda: scan_address_pages_cfg(bytes(code), {TABLE_PAGE}, {},
                                                 max_states=0),
                  "zero CFG state budget")


def run(main, output):
    synthetic_branch_path_write()
    synthetic_equivalent_branch_histories_merge()
    synthetic_distinct_register_states_do_not_merge()
    synthetic_call_barrier()
    synthetic_static_pointer_cells()
    synthetic_memory_loaded_alias()
    synthetic_counted_slot_loop()
    synthetic_limits()

    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["table"]["base"] == hex(TABLE_START)
    assert report["table"]["end_exclusive"] == hex(TABLE_END)
    cfg = report["branch_cfg_scan"]
    assert cfg["target_page_reference_budget_complete"] is True
    assert cfg["target_page_state_budget_exceeded"] is True
    assert cfg["target_page_cfg_complete"] is False
    direct_sites = {row["site"] for row in cfg["direct_accesses"]}
    assert {"0x116b8a0", "0x116b924"} <= direct_sites
    indexed_sites = {row["site"] for row in cfg["indexed_access_candidates"]}
    assert {
        "0x116b844", "0x116b9b0", "0x116ba2c", "0x116baf4",
        "0x116bbc0", "0x116bc88", "0x116bd54",
    } <= indexed_sites
    assert report["linear_baseline"]["all_baseline_witnesses_preserved"] is True
    loops = report["target_page_counted_slot_loops"]
    assert [row["site"] for row in loops] == [
        "0x116bf54", "0x116bfac",
    ]
    assert all(row["state"] == (
        "PROVEN_STATIC_LOOP_STRUCTURE_CONDITIONAL_ON_X20_PRESERVATION"
    ) for row in loops)
    assert [row["indirect_dispatch"]["target_load_offset"] for row in loops] == [
        0x60, 0x68,
    ]
    assert [row["loop_bytes_sha256"] for row in loops] == [
        "df7bdfbe579db712c6cb51a69ca69105acf2140a655759f462c2a6e896caa91b",
        "708f2801f32244ed5149582077bf1e4cc09c5a989c102dffd4b3445082a7b16e",
    ]
    for row in loops:
        assert row["counter"]["initial_value"] == 0
        assert row["counter"]["stride"] == 8
        assert row["counter"]["limit"] == 0x200
        assert row["counter"]["iteration_count_if_preserved"] == 64
        assert row["table_read"]["base"] == hex(TABLE_START)
        assert row["table_read"]["last_slot_if_counter_preserved"] == hex(TABLE_END - 8)
        assert row["table_read"]["end_exclusive_if_counter_preserved"] == hex(TABLE_END)
        assert row["indirect_dispatch"]["target_resolved"] is False
        assert row["indirect_dispatch"]["callee_preserves_x20_verified"] is False
        assert all(value is False for value in row["limits"].values())
    disassembly = report["target_page_budget_reference_disassembly"]
    assert [row["site"] for row in disassembly] == [
        "0x116bf54", "0x116bfac",
    ]
    assert [row["window_sha256"] for row in disassembly] == [
        "35246d71f911eb9179aaf35adabd7a48c503f39edd46e51940d0ea96cffbd26e",
        "0cb0fe2184caaf35f15df9931b964ee00198761bb6884b83f37d839210d23d12",
    ]
    for row in disassembly:
        assert row["instruction_count"] == 64
        assert 0 < row["decoded_instruction_count"] <= 64
        assert all(len(item["word_le"]) == 8 for item in row["rows"])
        assert sum(not item["decoded"] for item in row["rows"]) == (
            64 - row["decoded_instruction_count"]
        )
        assert any(
            edge["kind"] in {"conditional", "unconditional"}
            for item in row["rows"] for edge in item["edges"]
        )
    read_sites = {
        item["site"]: item
        for row in disassembly for item in row["rows"]
    }
    assert read_sites["0x116bf70"]["mnemonic"] == "ldr"
    assert read_sites["0x116bf70"]["operands"] == "x0, [x8, #0x28]"
    assert read_sites["0x116bfc8"]["mnemonic"] == "ldr"
    assert read_sites["0x116bfc8"]["operands"] == "x0, [x8, #0x28]"
    assert report["static_pointer_cells"]["bss_or_heap_cells_without_relocations_scanned"] is False
    for key, value in report["limits"].items():
        assert value is False, (key, value)

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_table_cfg.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_TABLE_CFG_PASS",
        "adrp_refs", cfg["page_reference_count"],
        "direct_accesses", len(cfg["direct_accesses"]),
        "indexed_accesses", len(cfg["indexed_access_candidates"]),
        "branch_path_writes", len(cfg["branch_path_table_writes"]),
        "static_pointer_cells", report["static_pointer_cells"]["candidate_cell_count"],
        "loaded_aliases", len(cfg["memory_loaded_aliases"]),
        "NO_ABI_NO_OWNER_NO_ARCHIVE_PRECEDENCE_NO_UZUY_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
