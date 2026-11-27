"""Real original ARM64 status5 call/data paths and helper body transcript."""
import argparse,json,struct,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_fileload_status import (
    inspect,STATUS_CALL_WITNESSES,STATUS_HELPER,MAIN_SHA256,
    SERVICE_WINDOW,SERVICE_ENTRYPOINTS,_service_words
)


def synthetic_service_window():
    raw=struct.pack("<II",0xD503201F,0xD65F03C0)
    rows=_service_words(raw,0,len(raw))
    assert [(x["mnemonic"],x["operands"]) for x in rows]==[
        ("nop",""),("ret","")]
    for start,end in ((1,8),(0,9),(8,4),(-4,4),(0,12)):
        try:_service_words(raw,start,end)
        except ValueError:pass
        else:raise AssertionError(("Invalid service window accepted",start,end))


def run(main,out):
    synthetic_service_window()
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
    service=report["service_code_window"]
    assert service["start"]==hex(SERVICE_WINDOW[0])
    assert service["end_exclusive"]==hex(SERVICE_WINDOW[1])
    assert service["window_bytes"]==SERVICE_WINDOW[1]-SERVICE_WINDOW[0]
    assert service["bounded_window_not_function_extent"]
    assert [int(x["at"],16) for x in service["entrypoints"]]==list(SERVICE_ENTRYPOINTS)
    assert len(service["instructions"])==service["window_bytes"]//4
    assert all(len(x["word_le"])==8 for x in service["instructions"])
    assert not service["lock_unlock_semantics_verified"]
    assert not service["service_function_boundaries_verified"]
    for key in ("service_semantics_verified",
                "mutex_lock_unlock_implementation_verified",
                "service_function_boundaries_verified",
                "service_runtime_binding_verified"):
        assert report[key] is False
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
    print("PINNED_FILELOAD_STATUS_SERVICE_WINDOW_PASS",
          service["start"],service["end_exclusive"],service["window_sha256"],
          "ENTRYPOINTS",[(x["at"],x["mnemonic"],x["operands"])
                         for x in service["entrypoints"]],
          "NO_LOCK_UNLOCK_SEMANTICS")
    for group in ("helper_code","file_open_return_handling_near_call"):
        for ins in report[group]["instructions"]:
            print("NATIVE_STATUS_PATH_WORD",group,ins["at"],ins["mnemonic"],ins["operands"])


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.main,a.output)
