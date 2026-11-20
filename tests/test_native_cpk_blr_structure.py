"""Test precise Capstone register chains and legacy BL callsite correction."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from portlib.native_cpk_blr_structure import inspect, MAIN_SHA256


def run(main,out):
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["main_sha256"]==MAIN_SHA256
    assert len(report["witnesses"])==7
    assert report["possible_indirect_method_offsets_bytes"]==[0x20,0x10]
    assert report["corrected_legacy_anchor"]["instruction_kind"]=="BL"
    assert report["corrected_legacy_anchor"]["address"]=="0x106f404"
    assert report["corrected_legacy_anchor"]["call_target"]=="0xfff6a0"
    assert report["candidate_entry_relocation"]["patch_slot"]=="0x215c478"
    assert not report["candidate_entry_relocation"]["function_entry_proven"]
    assert not report["ABI_verified"]
    assert not report["runtime_hook_installed"]
    assert not report["gameplay_verified"]
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);inp=root/"main";inp.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_cpk_blr_structure.py"),
             "--main",str(inp),"--output",str(root/"good")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((root/"good/native_cpk_blr_structure.json").read_text())==report
        changed=bytearray(raw);changed[256]^=1;inp.write_bytes(changed)
        cmd[-1]=str(root/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (root/"bad").exists()
        assert inp.read_bytes()==changed
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_cpk_blr_structure.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PINNED_ARM64_BLR_REGISTER_STRUCTURE",len(report["witnesses"]),
          "verified words",report["blr1_load_chain"],report["blr2_load_chain"],
          "candidate_entry",report["candidate_entry_relocation"],
          "corrected_callsite",report["corrected_legacy_anchor"],
          "lifecycle=UNKNOWN")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
