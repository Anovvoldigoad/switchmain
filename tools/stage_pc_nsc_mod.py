"""Termux: import a source-hash-verified PC NSC ZIP mod without overwrites."""
import argparse
from pathlib import Path
from portlib.pc_nsc_archive_stage import stage

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True,type=Path)
    p.add_argument("--sha256",required=True)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    r=stage(a.archive,a.sha256,a.output)
    print("PC_MOD_ARCHIVE_STAGED_ONLY",r["extracted_file_count"],
          r["source_archive_sha256"],
          "NOT_CONVERTED_TO_SWITCH_OR_GAMEPLAY")
if __name__=="__main__":
    main()
