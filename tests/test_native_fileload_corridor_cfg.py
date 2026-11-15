"""Pinned ARM64 corrected FileLoad path control flow and SHA guard."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_fileload_corridor_cfg import inspect,ENTRY,CALLS,MAIN_SHA256


def run(main,out):
    raw=main.read_bytes()
    result=inspect(raw)
    assert result["pinned_main_sha256"]==MAIN_SHA256
    assert result["original_entry_candidate"]==f"0x{ENTRY:x}"
    assert result["original_8_word_prologue_matches"]
    assert result["reachable_decoded_instruction_count"]>32
    assert len(result["named_callsite_witnesses"])==len(CALLS)
    assert all(x["actual_machine_word_BL_target_verified"]
               for x in result["named_callsite_witnesses"])
    for key in ("runtime_AAPCS64_function_signature_verified",
                "async_completion_verified","archive_lookup_priority_verified",
                "file_open_result_to_status5_causation_proven","native_hook_added",
                "gameplay_verified","full_moddingapi"):
        assert result[key] is False
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);src=root/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileload_corridor_cfg.py"),
             "--main",str(src),"--output",str(root/"good")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((root/"good/native_fileload_corridor_cfg.json").read_text())==result
        broken=bytearray(raw);broken[255]^=1;src.write_bytes(broken)
        cmd[-1]=str(root/"rejected")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (root/"rejected").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_corridor_cfg.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PINNED_FILELOAD_CFG_PASS",
          "reachable",result["reachable_decoded_instruction_count"],
          "named_calls",[(a["name"],a["syntactically_reachable_from_corrected_prologue"])
                         for a in result["named_callsite_witnesses"]],
          "outside_edges",len(result["out_of_window_control_flow_edges"]),
          "NO_NATIVE_HOOK_OR_GAMEPLAY")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();run(args.main,args.output)
