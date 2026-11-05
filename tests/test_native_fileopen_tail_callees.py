"""Original SHA-pinned eight FileOpen native tail callees and W0 proof."""
import argparse,json,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.native_fileopen_tail_callees import (
    inspect,_callee_report,_plt_import,EXPECTED_SITES,MAIN_SHA256)
from portlib.native_fileopen_tail import TAIL_TARGET

def negative_synthetic():
    # Exact A64 RET target and BL 0x20 from 0x00, in a standalone
    # tiny test code region. Not a real main image nor runtime ABI proof.
    code=bytearray(b"\x1f\x20\x03\xd5"*0x20)
    struct.pack_into("<I",code,0,0x94000008)
    struct.pack_into("<I",code,0x20,0xd65f03c0)
    assert _plt_import(code,bytearray(),{},0x20) is None
    record=_callee_report(code,bytearray(),{},0)
    assert record["direct_target"]=="0x20"
    assert record["bounded_target_cfg"]["return_sites"]==["0x20"]
    assert record["plt_import"] is None
    struct.pack_into("<I",code,0,0xd503201f)
    try:_callee_report(code,bytearray(),{},0)
    except ValueError:pass
    else:raise AssertionError("Non-BL native word classified as call")

def run(main,out):
    negative_synthetic()
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["source_main_sha256"]==MAIN_SHA256
    assert report["native_callsite_count"]==8
    assert report["eight_original_callsite_addresses"]==[
        hex(x) for x in EXPECTED_SITES]
    assert report["original_local_return_register_provenance"]["local_return_site"]=="0x115eca8"
    assert all(x["word_le"] and x["instruction"] for x in
               report["per_callsite_original_target_and_import_evidence"])
    for field in ("concrete_runtime_CRI_error_meaning_proven",
                  "ownership_allocator_rollback_proven",
                  "native_status_0x68_guard_0x1D8_lifecycle_proven",
                  "callback_lock_unlock_async_completion_proven",
                  "archive_priority_unbind_destructor_proven",
                  "native_hook_abi_safe_proven","native_patch_or_hook_added",
                  "full_moddingapi","ready_for_gameplay_test","emulator_tested",
                  "gameplay_verified"):
        assert report[field] is False
    with tempfile.TemporaryDirectory() as d:
        td=Path(d); source=td/"main";source.write_bytes(raw)
        command=[sys.executable,str(ROOT/"tools/audit_native_fileopen_tail_callees.py"),
                 "--main",str(source),"--output",str(td/"good")]
        r=subprocess.run(command,capture_output=True,text=True,check=True)
        assert "FILEOPEN_TAIL_EIGHT_CALLEES_STATIC_PASS 8" in r.stdout
        other=json.loads((td/"good/native_fileopen_tail_callees.json").read_text())
        assert other==report
        broken=bytearray(raw);broken[57]^=1;source.write_bytes(broken)
        command[-1]=str(td/"bad")
        assert subprocess.run(command,capture_output=True).returncode!=0
        assert not (td/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileopen_tail_callees.json").write_text(
        json.dumps(report,indent=2)+"\n")
    for x in report["per_callsite_original_target_and_import_evidence"]:
        print("EIGHT_CALLEE_NATIVE_WITNESS",x["site"],x["instruction"],
              x["direct_target"],
              x["plt_import"]["symbol"]["name"] if x["plt_import"] else "NO_PLT",
              "RET",x.get("bounded_target_cfg",{}).get("return_sites",[]),
              "ESC",x.get("bounded_target_cfg",{}).get("other_exits",[])[:5])
    print("FILEOPEN_TAIL_EIGHT_CALLEES_STATIC_PASS",
          report["native_callsite_count"],"NO_ABI_OR_GAMEPLAY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
