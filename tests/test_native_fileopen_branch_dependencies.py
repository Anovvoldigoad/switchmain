"""Original SHA-pinned FileOpen branch-edge and opaque-call regressions."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from portlib.native_fileopen_branch_dependencies import inspect, _reachable, _branch_census

class Dummy:
    def __init__(self,mnemonic,op_str=""):
        self.mnemonic=mnemonic;self.op_str=op_str

def synthetic():
    g={0:[("conditional",4),("fallthrough",8)],
       4:[("unconditional",16)],
       8:[("call",99),("fallthrough_after_call",12)],
       12:[("unconditional",20)],
       16:[("return_or_indirect_terminator",None)],
       20:[("return_or_indirect_terminator",None)]}
    d={p:Dummy(m) for p,m in [(0,"cbz"),(4,"b"),(8,"bl"),
                              (12,"b"),(16,"ret"),(20,"ret")]}
    got=_reachable(g,0,{16,20},0,24)
    assert set(got["reachable_returns"])=={16,20}
    edges=_branch_census(g,d,bytes(24),set(d),{16,20},0,24)
    assert len(edges)==1
    assert edges[0]["successors"][0]["syntactically_reaches_return"]==["0x10"]
    assert edges[0]["successors"][1]["syntactically_reaches_return"]==["0x14"]
    assert not edges[0]["feasibility_proven"]
    g[4]=[("unconditional",40)]
    edges=_branch_census(g,d,bytes(24),set(d),{16,20},0,24)
    assert edges[0]["successors"][0]["unresolved_or_out_of_window"]
    assert edges[0]["successors"][0]["syntactically_reaches_return"]==[]

def main(main,out):
    synthetic()
    raw=main.read_bytes()
    result=inspect(raw)
    assert result["bounded_return_literal_witnesses"][0]["constant_w0"]==1
    assert result["bounded_return_literal_witnesses"][1]["constant_w0"]==0
    assert result["reachable_instruction_count"]==52
    assert result["conditional_branch_edge_census"]
    assert result["reachable_external_callsite_census"]
    assert all(not x["feasibility_proven"] for x in
               result["conditional_branch_edge_census"])
    assert all(x["callee_effect_and_return_unknown"] for x in
               result["reachable_external_callsite_census"])
    for key in ("path_feasibility_or_CRI_error_semantics_proven",
                "callback_async_rollback_unbind_destructor_proven",
                "archive_priority_or_object_ownership_proven",
                "safe_hook_ABI_proven","native_hook_installed","gameplay_verified",
                "full_moddingapi"):
        assert result[key] is False
    with tempfile.TemporaryDirectory() as tmp:
        base=Path(tmp); src=base/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileopen_branch_dependencies.py"),
             "--main",str(src),"--output",str(base/"pass")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((base/"pass/native_fileopen_branch_dependencies.json").read_text())==result
        invalid=bytearray(raw); invalid[160]^=1;src.write_bytes(invalid)
        cmd[-1]=str(base/"reject")
        assert subprocess.run(cmd,capture_output=True).returncode!=0
        assert not (base/"reject").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileopen_branch_dependencies.json").write_text(
        json.dumps(result,indent=2)+"\n")
    print("FILEOPEN_BRANCH_DEPENDENCIES_STATIC_PASS",
          len(result["conditional_branch_edge_census"]),
          len(result["reachable_external_callsite_census"]),
          "NOT_CRI_OR_GAMEPLAY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();main(a.main,a.output)
