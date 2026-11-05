"""SHA-guarded original FileOpen 0x1170FB0 bounded W0 return census."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/"tools"))
from portlib.native_fileopen_returns import (
    inspect, _trace, _definition, MAIN_SHA256, INITIAL,
)


class Dummy:
    def __init__(self, mnemonic="nop", op_str="", writes=()):
        self.mnemonic, self.op_str, self.writes = mnemonic, op_str, writes

    def regs_access(self):
        return ([], list(self.writes))

    def reg_name(self, n):
        return {0:"w0", 1:"x0"}.get(n, "x1")


def test_synthetic_graphs():
    graph = {
        0:[("conditional",4),("fallthrough",8)],
        4:[("fallthrough",12)],
        8:[("fallthrough",12)],
        12:[("return_or_indirect_terminator",None)]
    }
    decoded = {0:Dummy("cbz","w1, #4"),
               4:Dummy("mov","w0, #0",(0,)),
               8:Dummy("mov","w0, #1",(0,)),
               12:Dummy("ret","")}
    result = _trace(graph, decoded, 0, 0, 16)
    assert result["returns"][12] == {"def@4","def@8"}
    assert result["definitions"][4]["w0_observed_value"] == 0
    assert result["definitions"][8]["w0_observed_value"] == 1
    graph[8] = [("call",0xdead),("fallthrough_after_call",12)]
    decoded[8] = Dummy("bl","#0xdead")
    result = _trace(graph, decoded, 0, 0, 16)
    assert result["returns"][12] == {"def@4","def@8"}
    assert result["definitions"][8]["w0_observed_value"] is None
    graph = {0:[("fallthrough",4)],4:[("conditional",0),
                                     ("fallthrough",8)],
             8:[("return_or_indirect_terminator",None)]}
    decoded = {0:Dummy(),4:Dummy("cbz","w1, #0"),
               8:Dummy("ret","")}
    result = _trace(graph, decoded, 0, 0, 12)
    assert result["returns"][8] == {INITIAL}
    assert result["reachable"] == {0,4,8}


def run(main, out):
    test_synthetic_graphs()
    raw = main.read_bytes()
    result = inspect(raw)
    assert result["main_sha256"] == MAIN_SHA256
    assert result["entry_candidate"] == "0x1170fb0"
    assert result["reachable_decoded_instructions"] >= 30
    assert result["reachable_decoded_instructions"] <= 384
    for ret in result["all_reachable_within_window_return_sites"]:
        assert ret["at"].startswith("0x")
        assert ret["reaching_w0_definitions"]
        assert not ret["actual_runtime_return_value_proven"]
    for field in ("native_CRI_zero_means_failure_proven",
                  "real_FileOpen_return_values_tested",
                  "all_function_exits_proven",
                  "X20_ownership_and_object_lifetime_proven",
                  "callback_async_unbind_or_archive_precedence_proven",
                  "hook_ABI_safe_proven", "hook_installed",
                  "Uzuy_tested", "gameplay_verified", "full_moddingapi"):
        assert result[field] is False
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); src=root/"main"; src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileopen_returns.py"),
             "--main",str(src),"--output",str(root/"ok")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((root/"ok/native_fileopen_returns.json").read_text()) == result
        bad=bytearray(raw);bad[255]^=1;src.write_bytes(bad)
        cmd[-1]=str(root/"invalid")
        assert subprocess.run(cmd,capture_output=True).returncode != 0
        assert not (root/"invalid").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileopen_returns.json").write_text(
        json.dumps(result,indent=2)+"\n")
    print("PINNED_FILEOPEN_ALL_BOUNDED_RETURN_PATHS_PASS",
          "reachable",result["reachable_decoded_instructions"],
          "RET",result["reachable_return_sites"],
          "def_sites",len(result["reaching_w0_definition_sites"]),
          "escapes",len(result["other_terminations_or_out_of_window"]),
          "NOT_REAL_CRI_OR_GAMEPLAY")


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
