"""Pinned original ARM64 bounded CFG, successors and SHA-fail-closed."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_cpk_cfg import inspect,REGIONS,_edges,_target,MAIN_SHA256


def run(main,out):
    assert _target("bl","#0xfff6a0")==0xfff6a0
    assert _target("b.eq","#0x100")==0x100
    assert _target("ldr","x8, [x8, #0x20]") is None
    assert _edges(0x100,"blr","x8")==[
        ("indirect_call_unresolved",None),("fallthrough_after_indirect_call",0x104)]
    assert _edges(0x100,"ret","")==[("return_or_indirect_terminator",None)]
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["main_sha256"]==MAIN_SHA256
    assert len(report["regions"])==len(REGIONS)
    assert report["function_boundaries_proven"] is False
    for name,reg in report["regions"].items():
        assert reg["reachable_decoded_words"]>0,name
        assert len(reg["decoded_reachable_instructions"])==reg["reachable_decoded_words"]
        assert reg["relative_relocation_incoming_count"]>=int(name!="file_open_1170fb0")
        assert reg["range_is_not_a_function_extent"]
        assert all(len(z["word_le"])==8 for z in reg["decoded_reachable_instructions"])
    assert report["native_hook_installed"] is False
    assert report["CRI_async_completion_verified"] is False
    assert report["gameplay_verified"] is False
    with tempfile.TemporaryDirectory() as path:
        d=Path(path);src=d/"main";src.write_bytes(raw)
        command=[sys.executable,str(R/"tools/audit_native_cpk_cfg.py"),
                 "--main",str(src),"--output",str(d/"ok")]
        subprocess.run(command,capture_output=True,check=True)
        assert json.loads((d/"ok/native_cpk_candidate_cfg.json").read_text())==report
        alt=bytearray(raw);alt[255]^=1;src.write_bytes(alt)
        command[-1]=str(d/"rejected")
        assert subprocess.run(command,capture_output=True).returncode!=0
        assert not (d/"rejected").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_cpk_candidate_cfg.json").write_text(json.dumps(report,indent=2)+"\n")
    for name,reg in report["regions"].items():
        print("NATIVE_CFG_PROOF",name,"reachable",reg["reachable_decoded_words"],
              "incoming_BL_B",reg["direct_B_BL_incoming_count"],
              "relocation_ptrs",reg["relative_relocation_incoming_slots"],
              "ret_or_branch_terms",reg["within_window_return_or_indirect_terminators"],
              "legacy_0x106f404_reachable",reg.get("legacy_callsite_syntactically_reachable"),
              "no_live_abi_or_async")
    print("PINNED_CFG_REJECT_BAD_SHA",True,"GAMETESTED=False")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.main,a.output)
