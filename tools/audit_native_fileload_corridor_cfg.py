#!/usr/bin/env python3
"""Read-only corrected native FileLoad entry/callsite CFG audit."""
import argparse,json
from pathlib import Path
from portlib.native_fileload_corridor_cfg import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True,help="New output directory")
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_fileload_corridor_cfg.json").write_text(json.dumps(report,indent=2)+"\n")
    print("FILELOAD_CORRECTED_CFG",report["original_entry_candidate"],
          "reachable_words",report["reachable_decoded_instruction_count"],
          "incoming",report["observed_direct_incoming_branch_count"],
          "witnesses",[(x["name"],x["syntactically_reachable_from_corrected_prologue"])
                       for x in report["named_callsite_witnesses"]],
          "ABI_ASYNC_GAMEPLAY=UNVERIFIED")


if __name__=="__main__":main()
