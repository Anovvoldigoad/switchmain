#!/usr/bin/env python3
"""Audit remaining four PC API raw payloads; not a Switch runtime adapter."""
import argparse
import json
from pathlib import Path
from portlib.pc_param_remaining import SOURCE, inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--family",choices=sorted(SOURCE),required=True)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--expected-sha256",required=True)
    p.add_argument("--output",type=Path,required=True,help="New report folder")
    args=p.parse_args()
    report=inspect(args.input.read_bytes(),args.family,args.expected_sha256)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"pc_remaining_parameter_audit.json").write_text(
        json.dumps(report,indent=2)+"\n")
    print("PASS_PC_SOURCE_FORMAT_ONLY",args.family,
          "rows",report["record_count"],"no Switch ABI/gameplay evidence")


if __name__=="__main__":
    main()
