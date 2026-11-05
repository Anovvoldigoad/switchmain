"""Cross-check public NSC 2.1.2.1 manager512 Git blob against native-derived PC prefix."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.pc_public_baseline import inspect,SOURCE_BYTES,SOURCE_GIT_BLOB_SHA1
from native_condition_fixture import baseline_from_main

def run(main,out):
    baseline,_=baseline_from_main(main)
    assert len(baseline)==SOURCE_BYTES
    result=inspect(baseline)
    assert result["original_git_blob_sha1"]==SOURCE_GIT_BLOB_SHA1
    assert result["merged_PC_517_authenticated"] is False
    assert result["stock_Switch_v170_CPK_authenticated"] is False
    assert result["emulator_tested"] is False
    with tempfile.TemporaryDirectory() as t:
        root=Path(t);path=root/"conditionprmManager.xfbin"
        path.write_bytes(baseline)
        cmd=[sys.executable,str(ROOT/"tools/verify_public_pc_baseline.py"),
             "--manager512",str(path),"--output",str(root/"good")]
        a=subprocess.run(cmd,capture_output=True,text=True,check=True)
        assert "PUBLIC_ORIGINAL_PC_MANAGER512_AUTHENTIC" in a.stdout
        assert json.loads((root/"good/pc_public_baseline.json").read_text())==result
        for damaged in (baseline+b"\x00",baseline[:-1],
                        baseline[:9]+bytes([baseline[9]^1])+baseline[10:]):
            path.write_bytes(damaged)
            bad=subprocess.run([*cmd[:-1],str(root/"bad")],capture_output=True)
            assert bad.returncode!=0
            assert not (root/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"pc_public_baseline.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PUBLIC_NSC_MANAGER512_GIT_SHA1_AND_SHA256_PASS",
          result["original_git_blob_sha1"],result["raw_sha256"],
          "NOT_MODDED_517_OR_SWITCH")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    run(a.main,a.output)
