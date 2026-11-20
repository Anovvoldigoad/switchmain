"""Pinned FileOpen BR provenance: positive, negative, boundary and byte proof."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from portlib.native_fileopen_br_provenance import analyze, slice_site
from portlib.native_cpk_graph import MAIN_SHA256


def check(main, output):
    pack = lambda *w: struct.pack("<" + "I"*len(w), *w)
    nop, ret = 0xd503201f, 0xd65f03c0
    code = pack(0xf9400001, 0xd61f0020)  # ldr x1,[x0]; br x1
    got = slice_site(code, 0, 4, "x1")
    assert got["definitions_reverse_order"][0]["mnemonic"] == "ldr"
    assert "x0" in got["unresolved_registers"]
    assert got["definitions_reverse_order"][0]["memory_operands"] == [
        {"base": "x0", "index": None, "displacement": 0,
         "value": "unknown_runtime_memory"}]
    offset = slice_site(pack(0xf9400c01, 0xd61f0020), 0, 4, "x1")
    assert offset["definitions_reverse_order"][0]["memory_operands"][0]["displacement"] == 24
    assert not offset["memory_dereferences_resolved"]
    assert not got["memory_dereferences_resolved"]
    barrier = slice_site(pack(ret, nop, 0xd61f0020), 0, 8, "x1")
    assert barrier["stop_reason"] == "control_flow_barrier"
    for data, at, reg in ((pack(nop, nop), 4, "x1"),
                          (code, 4, "x2"),
                          (code, 5, "x1")):
        try:
            slice_site(data, 0, at, reg)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid branch accepted")
    for limit in (0, 129):
        try:
            slice_site(code, 0, 4, "x1", limit=limit)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid limit accepted")
    original = main.read_bytes()
    assert hashlib.sha256(original).hexdigest() == MAIN_SHA256
    report = analyze(original)
    assert set(report["sites"]) == {"fileopen_br_x1", "fileopen_br_x2"}
    assert not report["ownership_verified"] and not report["gameplay_verified"]
    mutated = bytearray(original)
    mutated[-1] ^= 1
    try:
        analyze(mutated)
    except ValueError:
        pass
    else:
        raise AssertionError("Mutated source accepted")
    assert hashlib.sha256(main.read_bytes()).hexdigest() == MAIN_SHA256
    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileopen_br_provenance.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PINNED_FILEOPEN_BR_PROVENANCE_PASS", len(report["sites"]), "NO_ABI")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--main", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    check(a.main, a.output)
