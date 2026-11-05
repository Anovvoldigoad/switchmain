"""Termux explicit source-pinned multi-mod CPK candidate staging, no game patch."""
import argparse,json
from pathlib import Path
from portlib.pc_nsc_cpk_candidates import assemble

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spec",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=assemble(json.loads(a.spec.read_text()),a.output)
    print("PC_NSC_CPK_CANDIDATES_STAGED",report["candidate_cpk_count"],
          "CPKs",report["unique_CPK_TOC_paths"],"unique TOC paths",
          "NOT_INSTALLABLE_OR_GAMEPLAY")
if __name__=="__main__":
    main()
