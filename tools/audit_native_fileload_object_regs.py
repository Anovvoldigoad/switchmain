#!/usr/bin/env python3
"""Original pinned FileLoad X20/X22 bounded register-origin census."""
import argparse,json
from pathlib import Path
from portlib.native_fileload_object_regs import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    proof=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_fileload_object_regs.json").write_text(
        json.dumps(proof,indent=2)+"\n")
    for r in ("x20","x22"):
        names=list(proof["register_traces"][r]["sites"])
        print("ORIGINAL_REGISTER_ORIGINS",r,
              [(s,len(proof["register_traces"][r]["sites"][s]["possible_reaching_writes"]))
               for s in names],
              "writes",len(proof["register_traces"][r]["definition_sites"]),
              "NO_OWNERSHIP_OR_GAMEPLAY")
    print("PINNED_ORIGINAL_OBJECT_REG_AUDIT_PASS")


if __name__=="__main__":
    main()
