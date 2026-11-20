"""Exact pinned native main census, with synthetic ARM64 address-formation regression."""
import argparse
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "tools"))
from portlib.native_pc_family_xrefs import scan, adrp_add_target
from portlib.native_cpk_graph import MAIN_SHA256
from portlib.pc_api_manifest import ALL_FAMILIES

def enc_adrp(pc, target, reg):
    pages = ((target & ~4095) - (pc & ~4095)) >> 12
    assert -(1 << 20) <= pages < (1 << 20)
    bits = pages & ((1 << 21) - 1)
    return 0x90000000 | ((bits & 3) << 29) | ((bits >> 2) << 5) | reg

def enc_add(target, reg, shift=0):
    imm = (target & 4095) if not shift else (target >> 12) & 4095
    return 0x91000000 | (shift << 22) | (imm << 10) | (reg << 5) | reg

def run(main, out):
    for pc, target, reg in [(0x12000, 0x143a0, 0), (0x800000, 0x7feabc, 23),
                            (0x10000, 0x10000, 31)]:
        a, b = enc_adrp(pc, target, reg), enc_add(target, reg)
        assert adrp_add_target(a, b, pc) == target
        if reg != 31:
            assert adrp_add_target(a, b ^ 1, pc) is None
        assert adrp_add_target(0xd503201f, b, pc) is None
        assert adrp_add_target(a, 0xd503201f, pc) is None
    source = main.read_bytes()
    assert hashlib.sha256(source).hexdigest() == MAIN_SHA256
    report = scan(source)
    assert set(report["families"]) == ALL_FAMILIES
    assert report["family_count"] == 9
    assert len(report["segment_sha256"]) == 3
    assert not report["native_consumer_abi_verified"]
    assert not report["ownership_lifecycle_verified"]
    assert not report["archive_precedence_verified"]
    assert hashlib.sha256(main.read_bytes()).hexdigest() == MAIN_SHA256
    wrong = bytearray(source)
    wrong[-1] ^= 1
    try:
        scan(wrong)
    except ValueError:
        pass
    else:
        raise AssertionError("Tampered original main was accepted")
    with tempfile.TemporaryDirectory() as td:
        from subprocess import run as invoke
        target = Path(td) / "proof"
        command = [sys.executable, str(R / "tools" / "audit_native_pc_family_xrefs.py"),
                   "--main", str(main), "--output", str(target)]
        result = invoke(command, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert json.loads((target / "native_pc_family_xrefs.json").read_text()) == report
        assert hashlib.sha256(main.read_bytes()).hexdigest() == MAIN_SHA256
    out.mkdir(parents=True, exist_ok=True)
    (out / "native_pc_family_xrefs.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PINNED_NATIVE_PC_FAMILY_XREFS_PASS", report["family_count"],
          "families", report["direct_reference_count"], "candidate references NO_ABI")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--main", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    run(a.main, a.output)
