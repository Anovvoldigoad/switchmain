"""Verify source SHA and X8 indirect-tail pointer provenance, not runtime ABI."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.native_fileopen_dispatch_objects import inspect,DISPATCHES,MAIN_SHA256

def run(main,out):
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["original_main_sha256"]==MAIN_SHA256
    assert report["original_dispatch_corridor_count"]==2
    assert [int(x["original_br_site"],16) for x in report["dispatch_origins"]]==[
        i["branch"] for i in DISPATCHES]
    assert [x["indirect_method_field_offset"] for x in report["dispatch_origins"]]==[0xC0,0x58]
    for item in report["dispatch_origins"]:
        assert item["X8_nearest_syntactic_original_writers"]["consulted_register"]=="x8"
        assert item["X8_nearest_syntactic_original_writers"]["possible_immediate_reaching_writers"]
        assert item["original_load_instruction"].startswith("ldr x")
        assert len(item["original_load_word_le"])==8
        assert item["original_instruction_transcript"]
        assert item["actual_target_code_pointer_value_observed"] is False
        assert item["real_CRI_interface_dispatch_proven"] is False
        assert item["runtime_constructor_destructor_or_async_owner_proven"] is False
    for k in ("actual_runtime_object_ownership_proven",
              "actual_native_archive_priority_or_unbind_proven",
              "actual_CRI_lock_unlock_async_completion_proven",
              "hook_installation_safe_proven","native_hook_added",
              "gameplay_verified","full_moddingapi",
              "ready_for_gameplay_test","emulator_tested"):
        assert report[k] is False
    with tempfile.TemporaryDirectory() as root:
        folder=Path(root);source=folder/"main";source.write_bytes(raw)
        cmd=[sys.executable,str(ROOT/"tools/audit_native_fileopen_dispatch_objects.py"),
             "--main",str(source),"--output",str(folder/"okay")]
        completed=subprocess.run(cmd,capture_output=True,text=True,check=True)
        assert "NATIVE_FILEOPEN_DISPATCH_OBJECTS_PASS 2" in completed.stdout
        assert json.loads((folder/"okay/native_fileopen_dispatch_objects.json").read_text())==report
        wrong=bytearray(raw);wrong[81]^=1;source.write_bytes(wrong)
        cmd[-1]=str(folder/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode!=0
        assert not (folder/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileopen_dispatch_objects.json").write_text(
        json.dumps(report,indent=2)+"\n")
    for item in report["dispatch_origins"]:
        print("ORIGINAL_X8_DISPATCH_BASE",item["original_load_site"],
              [(w["at"],w["instruction"]) for w in item[
              "X8_nearest_syntactic_original_writers"]["possible_immediate_reaching_writers"]])
    print("NATIVE_FILEOPEN_DISPATCH_OBJECTS_PASS",2,"NO_CRI_OR_GAMEPLAY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
