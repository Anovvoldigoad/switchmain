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
    assert all(not x["path_feasibility_verified"] and
               not x["source_reachability_verified"] for x in summary)
    # External jump to a RET before the BR does not reach the BR.
    terminal = inbound_census(pack(nop, 0xd65f03c0, 0xd61f0020, 0x17fffffe),
                              0, {"site": (8, "x1")}, 2)
    assert terminal["sites"]["site"]["external_entry_path_summary"] == [{
        "target": "0x4", "incoming_edges": 1, "call_edges": 0,
        "jump_edges": 1, "conditional_edges": 0,
        "syntactic_path_from_target_to_br": False, "window_words_visited": 1,
        "source_reachability_verified": False, "path_feasibility_verified": False}]
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
        assert len({x["target"] for x in groups}) == len(groups)
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
