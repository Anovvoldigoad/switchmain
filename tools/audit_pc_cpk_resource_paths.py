#!/usr/bin/env python3
"""Read-only exact-name PC raw audio/effect candidate against CPK TOC indices.

JSON spec:
{"sources":[{"family":"bgmManagerParam","path":"/PC/bgmManagerParam.xfbin",
 "sha256":"..."}],
 "archives":[{"label":"patch170_sound","path":"/romfs/data/patch/170/sound.cpk",
 "sha256":"..."}]}
Record source/CPK hashes outside this tool; it refuses unpinned inputs.
"""
import argparse
import json
from pathlib import Path
from portlib.pc_cpk_resource_audit import audit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spec",type=Path,required=True)
    p.add_argument("--require-all-nine",action="store_true")
    p.add_argument("--output",type=Path,required=True,help="New report directory")
    args=p.parse_args()
    spec=json.loads(args.spec.read_text())
    if type(spec)!=dict or set(spec)!={"sources","archives"}:
        raise ValueError("Only sources and archives keys accepted")
    report=audit(spec["sources"],spec["archives"],args.require_all_nine)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"pc_cpk_resource_paths.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PC_CPK_RESOURCE_PATH_EVIDENCE",
          "PC candidates",report["PC_resource_name_candidates"],
          "literal TOC hits",report["literal_case_sensitive_TOC_hit_candidates"],
          "ambiguous archive duplicates",report["cross_archive_duplicate_literal_path_candidates"],
          "casefold-only",report["casefold_only_candidates"],
          "runtime resource resolution NOT PROVEN")


if __name__=="__main__":main()
