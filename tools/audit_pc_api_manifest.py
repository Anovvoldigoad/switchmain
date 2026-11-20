#!/usr/bin/env python3
"""Compose 1-9 SHA-pinned raw PC API files into a NON-NATIVE evidence manifest.

Spec JSON: {"sources":[{"family":"bgmManagerParam",
  "path":"/path/to/PC/raw/bgmManagerParam.xfbin",
  "sha256":"64 lowercase hex digits"}]}
No input bytes are changed; does not build an installable Switch mod.
"""
import argparse,json
from pathlib import Path
from portlib.pc_api_manifest import build_manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spec",type=Path,required=True)
    p.add_argument("--require-all-nine",action="store_true")
    p.add_argument("--output",type=Path,required=True,help="New report directory")
    a=p.parse_args()
    spec=json.loads(a.spec.read_text())
    if type(spec)!=dict or set(spec)!={"sources"}:
        raise ValueError("Only sources list accepted in input spec")
    report=build_manifest(spec["sources"],require_all_nine=a.require_all_nine)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"pc_api_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PC_FAMILY_MANIFEST_OK",report["PC_raw_family_count"],
          "unresolved_resource_name_candidates",
          report["unresolved_audio_effect_name_count"],
          "native_runtime=NOT_VERIFIED gameplay=NOT_TESTED")


if __name__=="__main__":main()
