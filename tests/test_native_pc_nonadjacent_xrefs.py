"""Nonadjacent original-main ARM64 evidence; synthetic false-positive controls."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "tools"))
from portlib.native_pc_nonadjacent_xrefs import analyze, candidate_pairs
from portlib.native_cpk_graph import MAIN_SHA256


def adrp(pc, target, reg):
    pages = ((target & ~4095) - (pc & ~4095)) >> 12
    bits = pages & ((1 << 21)-1)
    return 0x90000000 | ((bits & 3) << 29) | ((bits >> 2) << 5) | reg


def add(target, reg):
    return 0x91000000 | ((target & 4095) << 10) | (reg << 5) | reg


def run(main, out):
    pc, target, reg = 0x10000, 0x14234, 9
    a, b = adrp(pc, target, reg), add(target, reg)
    pack = lambda *words: struct.pack("<" + "I"*len(words), *words)
    nop, ret = 0xd503201f, 0xd65f03c0
    names = {target: ["synthetic"]}
    assert len(candidate_pairs(pack(a, nop, b, ret), pc, names)) == 1
    assert candidate_pairs(pack(a, 0x91000529, b, ret), pc, names) == []
    assert candidate_pairs(pack(a, ret, b), pc, names) == []
    assert candidate_pairs(pack(a, nop, b), pc, names, window=1) == []
    assert candidate_pairs(pack(a, nop, b), pc, {target+4: ["other"]}) == []
    for window in (0, 33):
        try:
            candidate_pairs(pack(a, b), pc, names, window=window)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid window accepted")
    source = main.read_bytes()
    assert hashlib.sha256(source).hexdigest() == MAIN_SHA256
    result = analyze(source)
    assert result["main_sha256"] == MAIN_SHA256
    assert len(result["segment_sha256"]) == 3
    assert not result["native_consumer_abi_verified"]
    assert not result["ownership_lifecycle_verified"]
    assert not result["archive_precedence_verified"]
    assert not result["gameplay_verified"]
    tampered = bytearray(source)
    tampered[-1] ^= 1
    try:
        analyze(tampered)
    except ValueError:
        pass
    else:
        raise AssertionError("Tampered main accepted")
    assert hashlib.sha256(main.read_bytes()).hexdigest() == MAIN_SHA256
    out.mkdir(parents=True, exist_ok=True)
    (out / "native_pc_nonadjacent_xrefs.json").write_text(json.dumps(result, indent=2)+"\n")
    print("PINNED_NONADJACENT_PC_XREFS_PASS", result["bounded_reference_count"], "NO_ABI")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--main", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    run(a.main, a.output)
