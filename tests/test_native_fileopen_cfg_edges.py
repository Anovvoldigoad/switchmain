"""Falsifiable bounded ARM64 direct-edge evidence, including authentic main pin."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from portlib.native_fileopen_cfg_edges import analyze, census, decode_edge, reaching_writers, trace_copy_origins
from portlib.native_cpk_graph import MAIN_SHA256


def check(main, output):
    pack = lambda *words: struct.pack("<" + "I" * len(words), *words)
    # cbz x0, +8; nop; b +8; nop; br x1 -- two paths converge at BR.
    code = pack(0xb4000040, 0xd503201f, 0x14000002, 0xd503201f, 0xd61f0020)
    got = census(code, 0, 16)
    assert got["site_in_window_predecessors"] == ["0x8", "0xc"]
    assert any(x["address"] == "0x8" for x in got["in_window_merges"])
    assert any(x["kind"] == "conditional" and x["to"] == "0x8" for x in got["direct_edges"])
    assert got["site_reachable_from_window_start"]
    assert got["window_entry_reachable_instructions"] == 4
    assert got["window_entry_reachable_merges"] == ["0x8"]
    dead = census(pack(0x14000002, 0xd503201f, 0xd61f0020), 0, 8)
    assert dead["window_entry_reachable_instructions"] == 2
    assert dead["site_reachable_from_window_start"]
    assert dead["window_entry_reachable_merges"] == []
    assert not got["complete_cfg_proven"] and not got["memory_values_proven"]
    assert decode_edge(0x14000000, 4) == ("jump", 4, False)
    assert decode_edge(0x17ffffff, 4) == ("jump", 0, False)
    assert decode_edge(0x94000001, 4) == ("call", 8, True)
    assert decode_edge(0xd61f0020, 16) == ("indirect_or_return", None, False)
    assert decode_edge(0xd63f0020, 16) == ("indirect_call", None, True)
    for authenticated_return in (0xd65f0bff, 0xd65f0fff):
        assert decode_edge(authenticated_return, 0) == ("indirect_or_return", None, False)
        terminal = census(pack(authenticated_return, 0xaa0203e1, 0xd61f0020), 0, 8)
        assert not terminal["site_reachable_from_window_start"]
        assert terminal["window_entry_reachable_instructions"] == 1
        unreachable = reaching_writers(pack(authenticated_return, 0xaa0203e1, 0xd61f0020), 0, 8, "x1")
        assert unreachable["writers"] == []
        assert unreachable["unknown_paths"] == ["site_not_reachable_from_window_entry"]
        assert not unreachable["memory_values_proven"] and not unreachable["abi_verified"]
    indirect = pack(0xd63f0020, 0xd61f0020)  # blr x1; br x1
    indirect_graph = census(indirect, 0, 4)
    assert indirect_graph["indirect_calls_unknown"] == ["0x0"]
    assert indirect_graph["site_reachable_from_window_start"]
    assert not indirect_graph["engine_consumer_abi_verified"]
    opaque = reaching_writers(indirect, 0, 4, "x1")
    assert "call_clobber_or_side_effect" in opaque["unknown_paths"]
    assert not opaque["writers"] and not opaque["abi_verified"]
    assert census(pack(0x14000020, 0xd61f0020), 0, 4)["out_of_window_edges"]
    for data, base, site, window in ((code, 0, 16, 0), (code, 0, 16, 513),
                                    (code, 0, 3, 4), (code, 2, 16, 4),
                                    (code, 0, 24, 4)):
        try:
            census(data, base, site, window)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid CFG window accepted")
    # Two reachable paths have distinct final x1 writers; no runtime value is inferred.
    diamond = pack(0xaa0203e1, 0xb4000040, 0xaa0303e1, 0xd61f0020)
    writers = reaching_writers(diamond, 0, 12, "x1")
    assert [x["address"] for x in writers["writers"]] == ["0x0", "0x8"]
    entry_writer = reaching_writers(pack(0xaa0203e1, 0xd61f0020), 0, 4, "x1")
    assert [x["address"] for x in entry_writer["writers"]] == ["0x0"]
    assert entry_writer["external_predecessors_unknown"] and not entry_writer["abi_verified"]
    entry_unknown = reaching_writers(pack(0xd503201f, 0xd61f0020), 0, 4, "x1")
    assert entry_unknown["writers"] == []
    assert entry_unknown["unknown_paths"] == ["hypothetical_window_entry"]
    assert not writers["abi_verified"] and writers["external_predecessors_unknown"]
    assert reaching_writers(pack(0xd503201f, 0xd61f0020), 0, 4, "x1")["unknown_paths"] == ["hypothetical_window_entry"]
    # Unreachable mov x1,x3 must not become a candidate writer.
    dead_writer = reaching_writers(pack(0x14000002, 0xaa0303e1, 0xd61f0020), 0, 8, "x1")
    assert dead_writer["writers"] == []
    assert "hypothetical_window_entry" in dead_writer["unknown_paths"]
    try:
        reaching_writers(diamond, 0, 12, "x2")
    except ValueError:
        pass
    else:
        raise AssertionError("Wrong indirect register accepted")
    # Source provenance is not the last writer alone: MOV x1<-x2<-x3<-x4
    # must record three distinct possible register dependencies.
    copy_chain = pack(0xaa0403e3, 0xaa0303e2, 0xaa0203e1, 0xd61f0020)
    origins = trace_copy_origins(copy_chain, 0, 12, "x1")
    assert [(node["address"], node["source_register"]) for node in origins["nodes"]] == [
        ("0x0", "x4"), ("0x4", "x3"), ("0x8", "x2")]
    assert all(node["kind"] == "register_copy" for node in origins["nodes"])
    assert "hypothetical_window_entry" in origins["unknown_paths"]
    assert origins["external_predecessors_unknown"]
    assert not origins["runtime_values_proven"] and not origins["consumer_abi_verified"]
    # Two reachable paths through a conditional merge have different x2
    # producers; these are alternatives rather than a proven runtime value.
    two_paths = pack(0xaa0403e2, 0xb4000040, 0xaa0303e2, 0xaa0203e1, 0xd61f0020)
    alternatives = trace_copy_origins(two_paths, 0, 16, "x1")
    assert {(node["address"], node.get("source_register")) for node in alternatives["nodes"]} == {
        ("0x0", "x4"), ("0x8", "x3"), ("0xc", "x2")}
    # A skipped writer and an opaque indirect call must never become evidence
    # for the value reaching the terminal BR.
    skipped = trace_copy_origins(pack(0x14000002, 0xaa0303e1, 0xd61f0020), 0, 8, "x1")
    assert skipped["nodes"] == []
    assert "hypothetical_window_entry" in skipped["unknown_paths"]
    call = trace_copy_origins(pack(0xaa0203e1, 0xd63f0060, 0xd61f0020), 0, 8, "x1")
    assert not call["nodes"] and "call_clobber_or_side_effect" in call["unknown_paths"]
    # LDR x2,[x0,#24] is a memory address form, not a known pointer value.
    memory = trace_copy_origins(pack(0xf9400c02, 0xaa0203e1, 0xd61f0020), 0, 8, "x1")
    assert memory["nodes"][0]["memory_address_forms"] == [
        {"base": "x0", "index": None, "displacement": 24}]
    assert memory["nodes"][0]["kind"] == "runtime_memory_load_or_operation"
    assert "runtime_memory_value_unknown" in memory["unknown_paths"]
    assert not memory["runtime_values_proven"]
    unreachable_origin = trace_copy_origins(pack(0xd65f0bff, 0xaa0203e1, 0xd61f0020),
                                            0, 8, "x1")
    assert unreachable_origin["nodes"] == []
    assert unreachable_origin["unknown_paths"] == ["site_not_reachable_from_window_entry"]
    try:
        trace_copy_origins(copy_chain, 0, 12, "x2")
    except ValueError:
        pass
    else:
        raise AssertionError("Copy-origin analysis accepted an incorrect BR register")
    original = main.read_bytes()
    assert hashlib.sha256(original).hexdigest() == MAIN_SHA256
    report = analyze(original)
    assert len(report["sites"]) == 2
    assert all(not x["complete_cfg_proven"] for x in report["sites"].values())
    for name, (site, register) in __import__("portlib.native_fileopen_br_provenance", fromlist=["SITES"]).SITES.items():
        evidence = report["sites"][name]["reaching_register_writers"]
        origins = report["sites"][name]["register_copy_origins"]
        assert origins["external_predecessors_unknown"]
        assert not origins["runtime_values_proven"] and not origins["consumer_abi_verified"]
        assert all(int(row["address"], 16) <= site and len(bytes.fromhex(row["bytes_le"])) == 4
                   for row in origins["nodes"])
        assert origins == trace_copy_origins(
            __import__("portlib.nso_profile", fromlist=["segments"]).segments(original)[0][1],
            __import__("portlib.nso_profile", fromlist=["segments"]).segments(original)[0][0],
            site, register)

        assert evidence["external_predecessors_unknown"] and not evidence["abi_verified"]
        assert not evidence["memory_values_proven"]
        assert all(int(row["address"], 16) <= site and len(bytes.fromhex(row["bytes_le"])) == 4
                   for row in evidence["writers"])
        assert evidence == reaching_writers(__import__("portlib.nso_profile", fromlist=["segments"]).segments(original)[0][1],
                                            __import__("portlib.nso_profile", fromlist=["segments"]).segments(original)[0][0], site, register)
    altered = bytearray(original)
    altered[-1] ^= 1
    try:
        analyze(altered)
    except ValueError:
        pass
    else:
        raise AssertionError("Unpinned original main accepted")
    assert hashlib.sha256(main.read_bytes()).hexdigest() == MAIN_SHA256
    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileopen_cfg_edges.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PINNED_FILEOPEN_CFG_EDGES_PASS", len(report["sites"]), "NO_ABI")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--main", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    check(a.main, a.output)
