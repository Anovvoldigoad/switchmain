"""Emit bounded original native FileOpen X0+0x18 tail handler evidence."""
import argparse,json
from pathlib import Path
from portlib.native_fileopen_tail import inspect
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"native_fileopen_tail.json").write_text(json.dumps(report,indent=2)+"\n")
    print("FILEOPEN_ORIGINAL_TAIL",report["original_fileopen_callsite"],
          "ADD_0x18",report["original_wrapper"],
          "B",report["original_native_tail_target"],
          "CMP_W0_1",report["original_fileopen_result_cmp"]["at"])
    for word in report["tail_window_original_first_words"][:24]:
        print(" FILEOPEN_TAIL_WORD",word["at"],word["word_le"],word["instruction"])
    g=report["tail_window_bounded_cfg"]
    print("FILEOPEN_TAIL_GRAPH",g["visited"],"returns",g["return_sites"],
          "calls",g["external_or_indirect_calls"],
          "escapes",g["other_exits"][:16],
          "memory",g["memory_access_samples"][:18],
          "NO_CRI_OR_GAMEPLAY")
if __name__=="__main__":main()
