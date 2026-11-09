"""Falsifiable bounded ARM64 direct-edge evidence, including authentic main pin."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from portlib.native_fileopen_cfg_edges import analyze, census, decode_edge
from portlib.native_cpk_graph import MAIN_SHA256


def check(main, output):
    pack = lambda *words: struct.pack("<" + "I" * len(words), *words)
    # cbz x0, +8; nop; b +8; nop; br x1 -- two paths converge at BR.
    code = pack(0xb4000040, 0xd503201f, 0x14000002, 0xd503201f, 0xd61f0020)
    got = census(code, 0, 16)
    assert got["site_in_window_predecessors"] == ["0x8", "0xc"]
    assert any(x["address"] == "0x8" for x in got["in_window_merges"])
    assert any(x["kind"] == "conditional" and x["to"] == "0x8" for x in got["direct_edges"])
    assert not got["complete_cfg_proven"] and not got["memory_values_proven"]
    assert decode_edge(0x14000000, 4) == ("jump", 4, False)
    assert decode_edge(0x17ffffff, 4) == ("jump", 0, False)
    assert decode_edge(0x94000001, 4) == ("call", 8, True)
    assert decode_edge(0xd61f0020, 16) == ("indirect_or_return", None, False)
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
    original = main.read_bytes()
    assert hashlib.sha256(original).hexdigest() == MAIN_SHA256
    report = analyze(original)
    assert len(report["sites"]) == 2
    assert all(not x["complete_cfg_proven"] for x in report["sites"].values())
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
