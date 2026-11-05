#!/usr/bin/env python3
"""Verify original ARM64 BLR register-read chains and a corrected callsite label."""
import argparse
import json
from pathlib import Path
from portlib.native_cpk_blr_structure import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True,help="New report directory")
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_cpk_blr_structure.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PINNED_ARM64_REGISTER_FLOW",report["witnesses"],
          "legacy_anchor",report["corrected_legacy_anchor"],
          "ENTRY_ABI_ASYNC_UNBIND=UNVERIFIED")


if __name__=="__main__":
    main()
