"""Real original ARM64 status5 call/data paths and helper body transcript."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_fileload_status import (
    inspect,STATUS_CALL_WITNESSES,STATUS_HELPER,MAIN_SHA256
)


def run(main,out):
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["main_sha256"]==MAIN_SHA256
    assert len(report["verified_status_argument_and_callsite_words"])==len(STATUS_CALL_WITNESSES)
    assert report["status_setter_candidate_target"]==f"0x{STATUS_HELPER:x}"
    assert report["second_sequence_read_error_field_offset"]==0x1d8
    assert report["second_sequence_compares_error_field_to"]==1
    assert not report["status_helper_object_field_write_verified"]
    assert not report["file_open_failed_path_to_status_helper_verified"]
    assert not report["ABI_safe_new_hook_proven"]
    assert not report["gameplay_verified"]
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);src=d/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileload_status.py"),
             "--main",str(src),"--output",str(d/"ok")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((d/"ok/native_fileload_status.json").read_text())==report
        altered=bytearray(raw);altered[255]^=1;src.write_bytes(altered)
        cmd[-1]=str(d/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (d/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_status.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NATIVE_STATUS5_CALLS_PASS",report["verified_status_argument_and_callsite_words"],
          "no gameplay or API hook")
    for group in ("helper_code","file_open_return_handling_near_call"):
        for ins in report[group]["instructions"]:
            print("NATIVE_STATUS_PATH_WORD",group,ins["at"],ins["mnemonic"],ins["operands"])


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.main,a.output)
