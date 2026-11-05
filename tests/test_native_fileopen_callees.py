"""Regression tests for exact original FileOpen callee/branch producers."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.native_fileopen_callees import (
    inspect, _writer_origins, _predecessors, _target_register, _callee_walk,
    MAIN_SHA256
)

class Fake:
    def __init__(self,m="nop",op="",wr=()):
        self.mnemonic=m
        self.op_str=op
        self.wr=wr
    def regs_access(self):
        return ([],list(self.wr))
    def reg_name(self,r):
        return {1:"w0",2:"nzcv",3:"x22"}.get(r,"x19")

def synthetic():
    d={0:Fake("cbz","x3, #0xc"),4:Fake("mov","w0, #1",(1,)),
       8:Fake("bl","#0x50"),12:Fake("cbz","w0, #0x14"),
       16:Fake("ret"),20:Fake("ret")}
    g={0:[("conditional",8),("fallthrough",4)],
       4:[("unconditional",12)],
       8:[("call",80),("fallthrough_after_call",12)],
       12:[("conditional",20),("fallthrough",16)],
       16:[("return_or_indirect_terminator",None)],
       20:[("return_or_indirect_terminator",None)]}
    pred=_predecessors(g,set(d),0,24)
    assert _target_register(d[12])=="x0"
    sources=_writer_origins(pred,d,12,"x0",entry=0)
    origins={(x["at"],x["kind"]) for x in sources["possible_immediate_reaching_writers"]}
    assert origins=={("0x4","native_instruction_write"),("0x8","unknown_call_clobber")}
    assert _target_register(Fake("b.ne","#0x20"))=="nzcv"
    d[4]=Fake("cmp","w8, #1")
    flags=_writer_origins(pred,d,12,"nzcv",entry=0)
    assert ("0x4","native_flag_setting_instruction") in {
        (x["at"],x["kind"]) for x in flags["possible_immediate_reaching_writers"]}
    bounded=_callee_walk(g,d,0,0,24)
    assert bounded["return_sites"]==["0x10","0x14"]
    assert bounded["external_or_indirect_calls"]==["0x8"]
    g[8]=[("unconditional",28)]
    bounded=_callee_walk(g,d,0,0,24)
    assert bounded["other_exits"]==[{"at":"0x1c","kind":"out_of_bounded_window"}]

def run(main,output):
    synthetic()
    raw=main.read_bytes()
    result=inspect(raw)
    assert result["original_main_sha256"]==MAIN_SHA256
    assert result["original_condition_site_count"]==3
    assert result["original_callsite_count"]==4
    assert all(not b["predicate_feasibility_proven"]
               for b in result["branch_sites_with_source_producers"])
    assert all(c["original_target_evidence"]["word_le"]
               for c in result["original_callsite_target_windows"])
    assert result["native_CRI_error_semantics_proven"] is False
    assert result["object_layout_and_ownership_proven"] is False
    assert result["safe_new_hook_ABI_proven"] is False
    assert result["emulator_tested"] is False
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); src=root/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(ROOT/"tools/audit_native_fileopen_callees.py"),
             "--main",str(src),"--output",str(root/"valid")]
        out=subprocess.run(cmd,capture_output=True,text=True,check=True)
        assert "FILEOPEN_CALLEE_SOURCE_STATIC_PASS 3 4" in out.stdout
        assert json.loads((root/"valid/native_fileopen_callees.json").read_text())==result
        damaged=bytearray(raw);damaged[175]^=1;src.write_bytes(damaged)
        cmd[-1]=str(root/"invalid")
        assert subprocess.run(cmd,capture_output=True).returncode != 0
        assert not (root/"invalid").exists()
    output.mkdir(parents=True,exist_ok=True)
    (output/"native_fileopen_callees.json").write_text(
        json.dumps(result,indent=2)+"\n")
    for row in result["original_callsite_target_windows"]:
        e=row["original_target_evidence"]
        cfg=e.get("bounded_callee_cfg",{})
        print("FILEOPEN_CALL_WITNESS",e["at"],e["instruction"],e["word_le"],
              "->",e["direct_original_target"],
              "RET",cfg.get("return_sites",[]),
              "ESCAPES",cfg.get("other_exits",[])[:5])
        for word in e.get("target_first_words",[])[:8]:
            print(" NATIVE_TARGET",word["at"],word["word_le"],word["instruction"])
    for row in result["branch_sites_with_source_producers"]:
        data=row["original_machine_condition_source"]
        print("FILEOPEN_BRANCH_WRITERS",row["at"],row["instruction"],
              data["consulted_register"],
              [(v["at"],v["instruction"]) for v in
              data["possible_immediate_reaching_writers"]])
    print("FILEOPEN_CALLEE_SOURCE_STATIC_PASS",3,4,"NOT_RUNTIME_OR_GAMEPLAY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    run(a.main,a.output)
