"""Original AArch64 FileOpen X0+0x18 tail target scope and failure guard."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.native_fileopen_tail import inspect,TAIL_TARGET,WRAPPER,MAIN_SHA256
def run(main,out):
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["original_main_sha256"]==MAIN_SHA256
    assert report["original_wrapper"]==hex(WRAPPER)
    assert report["original_native_tail_target"]==hex(TAIL_TARGET)
    assert report["original_wrapper_first_word_le"]=="00600091"
    assert report["original_tail_B_word_le"]=="eafbff17"
    assert report["original_imported_helper"]=="strncpy"
    assert report["original_fileopen_result_cmp"]["instruction"]=="cmp w0, #1"
    assert report["original_fileopen_result_cmp"]["following_original_branch"]["branch_taken_to_W0_zero_literal"]
    assert report["tail_window_bounded_cfg"]["visited"]>0
    assert report["tail_window_original_first_words"]
    for field in ("x0_pointer_plus_0x18_type_and_ownership_proven",
                  "tail_native_W0_semantics_proven",
                  "original_CRI_error_or_archive_failure_executed",
                  "real_callbacks_locks_async_unbind_destructor_proven",
                  "native_hook_ABI_safe_proven","new_native_hook_installed",
                  "gameplay_verified","full_moddingapi",
                  "ready_for_gameplay_test","emulator_tested"):
        assert report[field] is False
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);f=root/"main";f.write_bytes(raw)
        cmd=[sys.executable,str(ROOT/"tools/audit_native_fileopen_tail.py"),
             "--main",str(f),"--output",str(root/"ok")]
        p=subprocess.run(cmd,capture_output=True,text=True,check=True)
        assert "FILEOPEN_ORIGINAL_TAIL" in p.stdout
        assert json.loads((root/"ok/native_fileopen_tail.json").read_text())==report
        broken=bytearray(raw);broken[80]^=1;f.write_bytes(broken)
        cmd[-1]=str(root/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode != 0
        assert not (root/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileopen_tail.json").write_text(json.dumps(report,indent=2)+"\n")
    g=report["tail_window_bounded_cfg"]
    print("FILEOPEN_TAIL_MACHINE_PASS",
          report["original_native_tail_target"],
          "CFG_WORDS",g["visited"],
          "LOCAL_RET",g["return_sites"],
          "CALLEES",g["external_or_indirect_calls"],
          "EXITS",g["other_exits"][:10],
          "NOT_ABI_OR_GAMEPLAY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
