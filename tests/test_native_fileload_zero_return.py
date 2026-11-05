"""Original ARM64 FileOpen W0==0 conditional BL->status5 static witness."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_fileload_zero_return import inspect,MAIN_SHA256


def run(main,out):
    raw=main.read_bytes()
    q=inspect(raw)
    assert q["original_main_sha256"]==MAIN_SHA256
    assert q["file_open_zero_result_branch"]["following_branch"]=="0x116f480"
    assert q["file_open_zero_result_branch"]["zero_branch_target"]=="0x116f4d8"
    assert q["first_status5"]["target"]=="0x120661c"
    assert q["second_status5"]["target"]=="0x120661c"
    # Exact bounded original CFG result, not a runtime failure test.
    assert q["first_status5"]["reachable_from_CBZ_zero_taken"] is True
    assert q["second_status5"]["reachable_from_CBZ_zero_taken"] is False
    assert q["first_status5"]["syntactic_path_offsets"][0]=="0x116f4d8"
    assert q["second_status5"]["guarding_branch"]=="0x116f5b4 B.NE 0x116F5C4"
    assert not q["actual_CRI_file_open_failure_tested"]
    assert not q["safe_trampoline_ABI_verified"]
    assert not q["gameplay_verified"]
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);src=root/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileload_zero_return.py"),
             "--main",str(src),"--output",str(root/"ok")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((root/"ok/native_fileload_zero_return.json").read_text())==q
        broken=bytearray(raw);broken[255]^=1;src.write_bytes(broken);cmd[-1]=str(root/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (root/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_zero_return.json").write_text(json.dumps(q,indent=2)+"\n")
    print("ORIGINAL_FILEOPEN_ZERO_LINK_PASS",
          "first_status5_reachable",q["first_status5"]["reachable_from_CBZ_zero_taken"],
          "second_status5_reachable",q["second_status5"]["reachable_from_CBZ_zero_taken"],
          "NO_REAL_FILEOPEN_FAILURE_EXECUTION")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
