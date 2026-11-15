#!/usr/bin/env python3
"""Confirm actual original v1.70 A64 prologue at 0x116F404, not 0x106F404."""
import argparse,json
from pathlib import Path
from portlib.native_fileload_corrected_entry import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_fileload_corrected_entry.json").write_text(json.dumps(result,indent=2)+"\n")
    print("FILELOAD_0x100000_PROLOGUE_SOURCE_CORRECTION",result["prologue_candidate_verified"],
          "caller",result["commented_inbound_site"],"file_open",result["native_file_open_edge"])
    for word in result["nearby_instruction_window"]["words"]:
        at=int(word["at"],16)
        if 0x116F500<=at<=0x116F540 or 0x116F5A0<=at<=0x116F5E0:
            print("FILELOAD_CORRECTED_WORD",word["at"],word["word_le"],
                  word["mnemonic"],word["operands"])
    print("Function ABI, async, error source, unbind and priority UNPROVEN")


if __name__=="__main__":main()
