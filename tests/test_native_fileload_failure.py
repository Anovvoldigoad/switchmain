"""Reject invalid main, record real failure-corridor words and old hook mismatch."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_fileload_failure import (
    inspect,MAIN_SHA256,CORRIDOR_START,CORRIDOR_END,
    LEGACY_PROCESS_CALLSITE,LEGACY_CALL_TARGET
)


def run(main,out):
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["original_main_sha256"]==MAIN_SHA256
    assert not report["legacy_diagnostic_hook"]["source_fingerprint_matches_original_main"]
    assert report["legacy_diagnostic_hook"]["actual_instruction"]=="BL"
    assert report["legacy_diagnostic_hook"]["old_named_process_offset"]=="0x106f404"
    assert report["legacy_diagnostic_hook"]["actual_callee"]=="0xfff6a0"
    assert report["corridor"]["word_count"]==(CORRIDOR_END-CORRIDOR_START)//4
    assert report["corridor"]["old_file_open_failure_comment_site"]["at"]=="0x106f4d8"
    assert not report["status_5_branch_caused_by_file_open_failure_proven"]
    assert not report["safe_hook_relocation_or_installation_authorized"]
    assert not report["gameplay_verified"]
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);src=d/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileload_failure.py"),
             "--main",str(src),"--output",str(d/"ok")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((d/"ok/native_fileload_failure.json").read_text())==report
        changed=bytearray(raw);changed[255]^=1;src.write_bytes(changed)
        cmd[-1]=str(d/"rejected")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (d/"rejected").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_failure.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NATIVE_FILELOAD_CORRIDOR_PASS",report["corridor"]["word_count"],
          "word-exact instructions; stale hook fingerprint unsafe; ABI unknown")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.main,a.output)
