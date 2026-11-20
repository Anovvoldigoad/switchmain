#!/usr/bin/env python3
"""Static pinned FileOpen W0 zero return conditional CFG proof."""
import argparse,json
from pathlib import Path
from portlib.native_fileload_zero_return import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    r=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_fileload_zero_return.json").write_text(json.dumps(r,indent=2)+"\n")
    print("FILEOPEN_W0_ZERO_STATIC_LINK",r["file_open_zero_result_branch"],
          "status5_first_reachable",r["first_status5"]["reachable_from_CBZ_zero_taken"],
          "status5_second_reachable",r["second_status5"]["reachable_from_CBZ_zero_taken"],
          "NOT_RUNTIME_CRI_FAILURE_PROOF")


if __name__=="__main__":main()
