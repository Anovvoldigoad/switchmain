"""Authentic original-main direct external FileOpen edges plus synthetic regression."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileopen_external_edges import analyze, inbound_census
from portlib.native_fileopen_cfg_edges import decode_edge
from portlib.native_fileopen_br_provenance import SITES
from portlib.nso_profile import segments


def check(main, output):
    pack = lambda *words: struct.pack("<" + "I"*len(words), *words)
    nop = 0xd503201f
    # Entire text: external B 0->16, BL 4->24, B.cond 8->20,
    # and backward B 28->20 enter the 16..24 bounded window.
    code = pack(0x14000004, 0x94000005, 0x54000060, nop, nop, nop,
                0xd61f0020, 0x17fffffe, 0x14000008)
    report = inbound_census(code, 0, {"target": (24, "x1")}, 2)
    found = report["sites"]["target"]
    assert [(e["from"], e["to"], e["kind"]) for e in
            found["direct_inbound_from_outside_window"]] == [
                ("0x0", "0x10", "jump"), ("0x4", "0x18", "call"),
                ("0x8", "0x14", "conditional"), ("0x1c", "0x14", "jump")]
    assert found["direct_inbound_count"] == 4
    assert report["instruction_words_scanned"] == 9
    assert not report["complete_cfg_proven"] and not report["native_consumer_abi_verified"]
    assert not found["source_reachability_verified"]
    # In-window branches must not be counted as external predecessors.
    internal = inbound_census(pack(nop, 0x14000001, 0xd61f0020),
                              0, {"site": (8, "x1")}, 2)
    assert internal["sites"]["site"]["direct_inbound_count"] == 0
    # Incoming backward branch beyond bounded end, including the start boundary.
    backward = inbound_census(pack(nop, nop, 0xd61f0020, 0x17fffffd),
                              0, {"site": (8, "x1")}, 2)
    assert [(r["from"], r["to"]) for r in backward["sites"]["site"][
        "direct_inbound_from_outside_window"]] == [("0xc", "0x0")]
    # Group repeated external call sites by actual target and ask whether
    # any syntactic path from that target can reach BR (not whether it runs).
    summary = report["sites"]["target"]["external_entry_path_summary"]
    assert [(x["target"], x["incoming_edges"]) for x in summary] == [
        ("0x10", 1), ("0x14", 2), ("0x18", 1)]
    assert all(x["syntactic_path_from_target_to_br"] for x in summary)
    assert [[int(y["pc"], 16) for y in x["shortest_local_path"]] for x in summary] == [
        [16, 20, 24], [20, 24], [24]]
    assert [(x["noncall_inbound_edges"],
             x["noncall_inbound_call_free_candidate"]) for x in summary] == [
                 (1, True), (2, True), (0, False)]
    assert all(not x["noncall_inbound_candidate_runtime_verified"]
               for x in summary)
    assert all(x["call_free_syntactic_path_to_br"] for x in summary)
    assert [[int(y["pc"], 16) for y in x["shortest_call_free_path"]]
            for x in summary] == [[16, 20, 24], [20, 24], [24]]
    assert all(not x["path_call_side_effects_resolved"] for x in summary)
    assert all(len(x["call_free_register_effects"]) == len(x["shortest_call_free_path"]) for x in summary)
    assert all(not x["path_feasibility_verified"] and
               not x["source_reachability_verified"] for x in summary)
    # External jump to a RET before the BR does not reach the BR.
    terminal = inbound_census(pack(nop, 0xd65f03c0, 0xd61f0020, 0x17fffffe),
                              0, {"site": (8, "x1")}, 2)
    assert terminal["sites"]["site"]["external_entry_path_summary"] == [{
        "target": "0x4", "incoming_edges": 1, "call_edges": 0,
        "jump_edges": 1, "conditional_edges": 0,
        "syntactic_path_from_target_to_br": False, "window_words_visited": 1,
        "shortest_local_path": [], "call_free_syntactic_path_to_br": False,
        "call_free_window_words_visited": 1, "shortest_call_free_path": [], "call_free_register_effects": [],
        "path_call_side_effects_resolved": False,
        "source_reachability_verified": False, "path_feasibility_verified": False,
        "noncall_inbound_edges": 1,
        "noncall_inbound_call_free_candidate": False,
        "noncall_inbound_candidate_runtime_verified": False}]
    # A BL followed by BR is syntactically reachable only by assuming
    # the opaque call returns; never label that witness call-free.
    call_only = inbound_census(pack(nop, 0x94000001, 0xd61f0020,
                                    0x17fffffe), 0, {"site": (8, "x1")}, 2)
    call_group = call_only["sites"]["site"]["external_entry_path_summary"][0]
    assert call_group["syntactic_path_from_target_to_br"]
    assert not call_group["call_free_syntactic_path_to_br"]
    assert call_group["shortest_call_free_path"] == []
    assert call_group["call_free_register_effects"] == []
    # BLR also has opaque call effects and must not be labeled call-free.
    indirect_only = inbound_census(pack(nop, 0xd63f0020, 0xd61f0020,
                                        0x17fffffe), 0, {"site": (8, "x1")}, 2)
    indirect_group = indirect_only["sites"]["site"]["external_entry_path_summary"][0]
    assert indirect_group["syntactic_path_from_target_to_br"]
    assert not indirect_group["call_free_syntactic_path_to_br"]
    assert indirect_group["shortest_call_free_path"] == []
    assert indirect_group["call_free_register_effects"] == []
    # A conditional branch can bypass a BL; shortest call-free witness
    # must use the bypass rather than an opaque call fallthrough.
    bypass = inbound_census(pack(nop, 0x54000040, 0x94000001,
                                 0xd61f0020, 0x17fffffd),
                            0, {"site": (12, "x1")}, 3)
    bypass_group = bypass["sites"]["site"]["external_entry_path_summary"][0]
    assert bypass_group["call_free_syntactic_path_to_br"]
    assert [int(s["pc"], 16) for s in bypass_group["shortest_call_free_path"]] == [4, 12]
    # Exact ARM64 MOV X1,X2 before BR X1: preserve register effects without ABI inference.
    mov = inbound_census(pack(nop, 0xaa0203e1, 0xd61f0020, 0x17fffffe),
                         0, {"site": (8, "x1")}, 2)
    effects = mov["sites"]["site"]["external_entry_path_summary"][0]["call_free_register_effects"]
    assert effects[0]["bytes_le"] == pack(0xaa0203e1).hex()
    assert "x2" in effects[0]["register_reads"] and "x1" in effects[0]["register_writes"]
    assert not effects[0]["memory_operand_present"]
    # A cycle must terminate and remain unreachable.
    cycle = inbound_census(pack(nop, 0x14000000, 0xd61f0020, 0x17fffffe),
                           0, {"site": (8, "x1")}, 2)
    assert not cycle["sites"]["site"]["external_entry_path_summary"][0][
        "syntactic_path_from_target_to_br"]
    assert cycle["sites"]["site"]["external_entry_path_summary"][0]["window_words_visited"] == 1
    for payload, base, sites, window in [
        (code, 0, {}, 2), (code, 0, {"s": (24, "x1")}, 0),
        (code, 0, {"s": (24, "x1")}, 513),
        (code, 2, {"s": (24, "x1")}, 2),
        (code[:-1], 0, {"s": (24, "x1")}, 2),
        (code, 0, {"s": (23, "x1")}, 2),
        (code, 0, {"s": (24, "x2")}, 2),
        (code, 0, {"s": (36, "x1")}, 2),
        (code, 0, {"s": (24, "x31")}, 2),
    ]:
        try:
            inbound_census(payload, base, sites, window)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid edge-census input accepted")
    original = main.read_bytes()
    assert hashlib.sha256(original).hexdigest() == MAIN_SHA256
    authentic = analyze(original)
    base, text, _ = segments(original)[0]
    assert authentic["main_sha256"] == MAIN_SHA256
    assert authentic["text_sha256"] == hashlib.sha256(text).hexdigest()
    assert authentic["instruction_words_scanned"] == len(text)//4
    assert set(authentic["sites"]) == set(SITES)
    for name, (site, register) in SITES.items():
        entry = authentic["sites"][name]
        assert entry["site"] == hex(site) and entry["register"] == register
        assert not entry["native_consumer_abi_verified"]
        assert not entry["indirect_predecessors_resolved"]
        assert not entry["outside_text_predecessors_resolved"]
        assert entry["direct_inbound_count"] == len(entry["direct_inbound_from_outside_window"])
        groups = entry["external_entry_path_summary"]
        assert sum(x["incoming_edges"] for x in groups) == entry["direct_inbound_count"]
        assert all(x["noncall_inbound_edges"] == x["jump_edges"] +
                   x["conditional_edges"] for x in groups)
        assert all(x["noncall_inbound_call_free_candidate"] ==
                   bool(x["noncall_inbound_edges"] and
                        x["call_free_syntactic_path_to_br"]) for x in groups)
        assert all(not x["noncall_inbound_candidate_runtime_verified"]
                   for x in groups)
        assert len({x["target"] for x in groups}) == len(groups)
        for group in groups:
            witness = group["shortest_local_path"]
            call_free = group["shortest_call_free_path"]
            assert bool(call_free) == group["call_free_syntactic_path_to_br"]
            assert len(group["call_free_register_effects"]) == len(call_free)
            assert all(not e["runtime_register_values_verified"] and
                       not e["memory_ownership_verified"] for e in group["call_free_register_effects"])
            assert not call_free or bool(witness)
            for step in call_free[:-1]:
                pc = int(step["pc"], 16)
                raw = text[pc-base:pc-base+4]
                assert raw.hex() == step["bytes_le"]
                assert decode_edge(struct.unpack("<I", raw)[0], pc)[0] not in ("call", "indirect_call")
            assert bool(witness) == group["syntactic_path_from_target_to_br"]
            assert not group["path_call_side_effects_resolved"]
            if not witness:
                continue
            assert witness[0]["pc"] == group["target"] and witness[-1]["pc"] == hex(site)
            assert len(witness) <= group["window_words_visited"]
            for idx, step in enumerate(witness):
                pc = int(step["pc"], 16)
                raw = text[pc-base:pc-base+4]
                assert len(raw) == 4 and raw.hex() == step["bytes_le"]
                if idx+1 < len(witness):
                    nxt = int(witness[idx+1]["pc"], 16)
                    kind, destination, fallthrough = decode_edge(struct.unpack("<I", raw)[0], pc)
                    assert (destination == nxt and kind != "call") or (fallthrough and nxt == pc+4)
        assert all(not x["source_reachability_verified"] and
                   not x["path_feasibility_verified"] for x in groups)
        assert all(int(entry["window_start"], 16) <= int(x["target"], 16) <= site
                   for x in groups)

        start = int(entry["window_start"], 16)
        for row in entry["direct_inbound_from_outside_window"]:
            pc, target = int(row["from"], 16), int(row["to"], 16)
            assert base <= pc < base+len(text)
            assert start <= target <= site and not start <= pc <= site
            raw = text[pc-base:pc-base+4]
            assert raw.hex() == row["bytes_le"]
            kind, destination, _ = decode_edge(struct.unpack("<I", raw)[0], pc)
            assert (kind, destination) == (row["kind"], target)
            assert not row["source_reachability_verified"]
    altered = bytearray(original)
    altered[-1] ^= 1
    try:
        analyze(altered)
    except ValueError:
        pass
    else:
        raise AssertionError("Unpinned original main accepted")
    assert hashlib.sha256(main.read_bytes()).hexdigest() == MAIN_SHA256
    assert not authentic["ownership_verified"] and not authentic["archive_precedence_verified"]
    assert not authentic["gameplay_verified"]
    output.mkdir(parents=True, exist_ok=True)
    (output/"native_fileopen_external_edges.json").write_text(
        json.dumps(authentic, indent=2)+"\n")
    print("PINNED_FILEOPEN_EXTERNAL_EDGES_PASS", len(authentic["sites"]),
          "FULL_TEXT_NO_ABI")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--main", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    check(a.main, a.output)
