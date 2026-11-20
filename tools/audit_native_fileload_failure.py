#!/usr/bin/env python3
"""Pinned bounded native file-load error corridor and dormant-hook fingerprint."""
import argparse,json
from pathlib import Path
from portlib.native_fileload_failure import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_fileload_failure.json").write_text(json.dumps(report,indent=2)+"\n")
    print("FILELOAD_LEGACY_FINGERPRINT_MISMATCH",
          report["legacy_diagnostic_hook"])
    for w in report["corridor"]["instructions"]:
        if 0x106F490<=int(w["at"],16)<=0x106F518:
            print("FILELOAD_FAILURE_CORRIDOR_WORD",w["at"],w["bytes_le"],
                  w["mnemonic"],w["operands"])
    print("No async/status-field owner proof, no native hook installed.")


if __name__=="__main__":main()
