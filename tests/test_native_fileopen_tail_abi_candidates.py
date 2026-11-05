"""Exact-main FileOpen native callsite argument sources and branch writers."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.native_fileopen_tail_abi_candidates import (
    inspect,_reached,EXPECTED_SITES,MAIN_SHA256)
def synthetic():
    graph={0:[("fallthrough",4)],
           4:[("call",0x300),("fallthrough_after_call",8)],
           8:[("return_or_indirect_terminator",None)]}
    reached,escapes=_reached(graph,0,0,12)
    assert reached=={0,4,8} and not escapes
    graph[0]=[("unconditional",16)]
    reached,escapes=_reached(graph,0,0,12)
    assert reached=={0,16} and escapes==["0x10"]

def run(main,out):
    synthetic()
    raw=main.read_bytes()
    result=inspect(raw)
    assert result["source_main_sha256"]==MAIN_SHA256
    assert result["tail_bounded_reached_instructions"]==53
    assert len(result["callsite_provenance"])==8
    assert [int(r["site"],16) for r in result["callsite_provenance"]]==list(EXPECTED_SITES)
    assert all(set(r["source_tail_implicit_argument_register_writers"])==
               {"x0","x1","x2","x3"} for r in result["callsite_provenance"])
    assert all(x.get("original_machine_word_sample")
               for x in result["callsite_provenance"])
    for field in ("native_CRI_failure_state_proven",
                  "native_object_allocation_and_lifetime_proven",
                  "callback_lock_async_unbind_destructor_proven",
                  "archive_precedence_proven","new_hook_or_binary_patch_installed",
                  "safe_hook_abi_proven","full_moddingapi",
                  "ready_for_gameplay_test","emulator_tested","gameplay_verified"):
        assert result[field] is False
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);source=root/"main";source.write_bytes(raw)
        cmd=[sys.executable,str(ROOT/"tools/audit_native_fileopen_tail_abi_candidates.py"),
             "--main",str(source),"--output",str(root/"good")]
        cp=subprocess.run(cmd,capture_output=True,text=True,check=True)
        assert "FILEOPEN_ORIGINAL_ARG_BR_STATIC_PASS 8" in cp.stdout
        assert json.loads((root/"good/native_fileopen_tail_abi_candidates.json").read_text())==result
        bad=bytearray(raw);bad[87]^=1;source.write_bytes(bad)
        cmd[-1]=str(root/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode!=0
        assert not (root/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileopen_tail_abi_candidates.json").write_text(
        json.dumps(result,indent=2)+"\n")
    for item in result["callsite_provenance"]:
        print("ORIGINAL_NATIVE_TAIL_ARGS",item["site"],
              item["callee_target"],
              [(reg,[(x["at"],x["instruction"]) for x in
                 row["possible_immediate_reaching_writers"]])
               for reg,row in
               item["source_tail_implicit_argument_register_writers"].items()])
        print("ORIGINAL_NATIVE_TAIL_BRANCH_WRITERS",item["site"],
              [(x["at"],x.get("branch_register"),
                [(w["at"],w["instruction"]) for w in
                 x.get("possible_original_register_writers",{})
                  .get("possible_immediate_reaching_writers",[])])
               for x in item.get("native_indirect_br_register_sources",[])])
        for ins in item.get("original_machine_word_sample",[])[:12]:
            print("ORIGINAL_NATIVE_TARGET_BYTE",item["site"],ins["at"],
                  ins["word_le"],ins["instruction"])
    print("FILEOPEN_ORIGINAL_ARG_BR_STATIC_PASS",8,"NOT_CRI_ABI_OR_GAMEPLAY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
