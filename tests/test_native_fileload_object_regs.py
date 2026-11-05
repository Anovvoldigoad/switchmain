"""Pinned original AArch64 FileLoad X20/X22 writer-provenance analysis."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from portlib.native_fileload_object_regs import (
    inspect, _trace_register, MAIN_SHA256
)


class Dummy:
    def __init__(self,mnemonic="nop",op_str="",writes=()):
        self.mnemonic,self.op_str,self.writes=mnemonic,op_str,writes

    def regs_access(self):
        return ([],list(self.writes))

    def reg_name(self,n):
        return {1:"x20",2:"x22"}.get(n,"x0")


def synthetic():
    graph={0:[("conditional",4),("fallthrough",8)],
           4:[("fallthrough",12)],
           8:[("fallthrough",12)],
           12:[("return_or_indirect_terminator",None)]}
    ins={0:Dummy("cbz","w1, #4"),
         4:Dummy("mov","x20, x0",(1,)),
         8:Dummy("mov","x20, x3",(1,)),
         12:Dummy("ret","")}
    flow=_trace_register(graph,ins,"x20",0,{"merge":12},0,16)
    assert len(flow["sites"]["merge"]["possible_reaching_writes"])==2
    assert len(flow["definition_sites"])==2
    graph={0:[("fallthrough",4)],4:[("conditional",0),
                                        ("fallthrough",8)],
           8:[("return_or_indirect_terminator",None)]}
    ins={0:Dummy(),4:Dummy("cbz","x0, #0"),8:Dummy("ret","")}
    flow=_trace_register(graph,ins,"x22",0,{"exit":8},0,12)
    assert flow["sites"]["exit"]["possible_reaching_writes"][0]["kind"]==(
        "incoming_callee_saved_value")


def run(main,out):
    synthetic()
    raw=main.read_bytes()
    proof=inspect(raw)
    assert proof["original_main_sha256"]==MAIN_SHA256
    for key in ("first_status_X20_argument_move",
                "second_status_X20_argument_move"):
        assert proof["register_traces"]["x20"]["sites"][key]["possible_reaching_writes"]
    assert proof["register_traces"]["x22"]["sites"]["second_guard_X22_field_base"][
        "possible_reaching_writes"]
    for field in ("object_X20_type_or_lifetime_verified",
                  "X22_guard_context_type_verified",
                  "source_archive_priority_verified",
                  "native_CRI_async_unbind_and_destructor_verified",
                  "safe_hook_ABI_proven","hook_added",
                  "Uzuy_gameplay_verified","full_moddingapi"):
        assert proof[field] is False
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);src=root/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileload_object_regs.py"),
             "--main",str(src),"--output",str(root/"ok")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((root/"ok/native_fileload_object_regs.json").read_text())==proof
        wrong=bytearray(raw);wrong[255]^=1;src.write_bytes(wrong)
        cmd[-1]=str(root/"rejected")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (root/"rejected").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_object_regs.json").write_text(
        json.dumps(proof,indent=2)+"\n")
    for r in ("x20","x22"):
        t=proof["register_traces"][r]
        print("PINNED_OBJECT_REGISTER",r,"write_sites",
              [(x["at"],x["instruction"]) for x in t["definition_sites"]],
              "site_origins",
              {k:[x.get("at") for x in v["possible_reaching_writes"]]
               for k,v in t["sites"].items()})
    print("PINNED_OBJECT_REGISTER_ORIGINS_PASS",
          "NOT_CLASS_OR_LIFETIME_OR_GAMEPLAY")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
