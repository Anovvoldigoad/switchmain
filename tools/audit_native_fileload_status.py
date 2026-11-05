#!/usr/bin/env python3
"""Display exact status setter candidate and fileopen return corridor."""
import argparse,json
from pathlib import Path
from portlib.native_fileload_status import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_fileload_status.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NATIVE_STATUS5_ARGUMENT_WITNESSES",
          report["verified_status_argument_and_callsite_words"])
    for group in ("helper_code","file_open_return_handling_near_call"):
        for ins in report[group]["instructions"]:
            print("NATIVE_STATUS_HELPER_OR_OPEN",group,ins["at"],
                  ins["word_le"],ins["mnemonic"],ins["operands"])
    print("No new hook, lifetime, archive priority or gameplay proof")


if __name__=="__main__":main()
