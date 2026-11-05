"""Regression: exact pinned main, Capstone instruction transcript, BLR/BL witnesses."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from portlib.native_cpk_disasm import inspect, SITES, MAIN_SHA256


def run(main,out):
    original=main.read_bytes()
    result=inspect(original)
    assert result["source_main_sha256"]==MAIN_SHA256
    assert len(result["windows"])==len(SITES)
    assert result["known_blr_offsets"]==["0x106ed9c","0x106edd0"]
    assert result["known_file_open_direct_edge"]["target"]=="0x1170fb0"
    for name,row in result["windows"].items():
        assert row["length"]==len(row["words"])*4
        assert row["bounded_window_is_not_function_extent"]
        assert all(len(w["word_le"])==8 for w in row["words"])
        assert len(row["sha256_instructions_window"])==64
    assert not result["calling_convention_register_semantics_proven"]
    assert not result["native_hook_installed"]
    assert not result["gameplay_verified"]
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);source=root/"main";source.write_bytes(original)
        cmd=[sys.executable,str(R/"tools/audit_native_cpk_disasm.py"),
             "--main",str(source),"--output",str(root/"good")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((root/"good/native_cpk_disassembly.json").read_text())==result
        broken=bytearray(original);broken[256]^=1;source.write_bytes(broken)
        cmd[-1]=str(root/"rejected")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (root/"rejected").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_cpk_disassembly.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PINNED_CPK_DISASSEMBLY_PASS",len(result["windows"]),
          "bounded windows, original main hash verified, no runtime proof")
    for name,row in result["windows"].items():
        interesting=[(x["code_offset"],x["mnemonic"],x["operands"])
                     for x in row["words"] if x["mnemonic"].lower()
                     in ("blr","br","bl","ret","ldr","adrp","adr","add")]
        print("PINNED_ARM64_CONTEXT",name,
              "anchor",row["anchor"],
              "window_sha256",row["sha256_instructions_window"],
              "selected_instructions",interesting[:18])


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
