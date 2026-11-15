#!/usr/bin/env python3
"""Android/Termux: hash genuine input files then run paired stock/raw176 audit.

Example:
 python tools/audit_real_condition_intake.py \
 --discover-manager-root /storage/emulated/0/Download \
 --stock-cpk /storage/emulated/0/Download/SWITCH/EXTRACTED_GAME/READY_TO_MOD/romfs/data/patch/170/common.cpk \
 --candidate-cpk /storage/emulated/0/Download/MY_MOD/romfs/data/patch/170/common.cpk \
 --output /storage/emulated/0/Download/CPK_517_EVIDENCE

Never modifies inputs and never declares an archive untouched stock solely
from its filename or hash. Without the actual original merged 517 manager
or candidate archive, the audit refuses to produce a fabricated success.
"""
import argparse
import json
from pathlib import Path
from portlib.real_condition_intake import discover_manager,inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--pc-manager",type=Path)
    m.add_argument("--discover-manager-root",type=Path)
    p.add_argument("--stock-cpk",required=True,type=Path)
    p.add_argument("--candidate-cpk",required=True,type=Path)
    p.add_argument("--expected-pc-manager-sha256")
    p.add_argument("--expected-stock-sha256")
    p.add_argument("--expected-candidate-sha256")
    p.add_argument("--output",required=True,type=Path,help="New directory, outside originals")
    a=p.parse_args()
    path=a.pc_manager if a.pc_manager else discover_manager(a.discover_manager_root)
    result=inspect(path,a.stock_cpk,a.candidate_cpk,
                   a.expected_pc_manager_sha256,a.expected_stock_sha256,
                   a.expected_candidate_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"real_condition_intake.json").write_text(json.dumps(result,indent=2)+"\n")
    print("REAL_INPUT_BYTE_AUDIT",result["pc_manager"]["sha256"],
          result["stock_cpk"]["sha256"],result["candidate_cpk"]["sha256"],
          "stock_prefix_unchanged",result["audit"]["native_values_preserved"],
          "source_provenance_verified=NO gameplay_verified=NO")


if __name__=="__main__":main()
