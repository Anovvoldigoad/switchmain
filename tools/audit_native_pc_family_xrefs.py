#!/usr/bin/env python3
"""Read-only nine-family literal/xref census against original Switch v1.70 main."""
import argparse
import json
from pathlib import Path
from portlib.native_pc_family_xrefs import scan

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    report = scan(a.main.read_bytes())
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output / "native_pc_family_xrefs.json").write_text(json.dumps(report, indent=2) + "\n")
    print("NATIVE_PC_FAMILY_LITERAL_CENSUS", report["direct_reference_count"],
          "adjacent candidates; NOT ABI PROOF")

if __name__ == "__main__":
    main()
