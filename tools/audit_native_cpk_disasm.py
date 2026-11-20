#!/usr/bin/env python3
"""Read-only disassembly of pinned ARM64 FileLoad and CPK candidate sites."""
import argparse
import json
from pathlib import Path
from portlib.native_cpk_disasm import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path,help="New report directory")
    a=p.parse_args()
    result=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_cpk_disassembly.json").write_text(json.dumps(result,indent=2)+"\n")
    for name,row in result["windows"].items():
        print("CPK_DISASM",name,row["anchor"],"SHA256",row["sha256_instructions_window"])
        for ins in row["words"]:
            if name in ("indirect_blr_1","indirect_blr_2",
                        "relocated_candidate_1","relocated_candidate_3"):
                print("CPK_ARM64_WORD",name,ins["code_offset"],
                      ins["word_le"],ins["mnemonic"],ins["operands"])
    print("STATIC DISASSEMBLY ONLY: no CPK async/unbind or gameplay proof.")


if __name__=="__main__":main()
