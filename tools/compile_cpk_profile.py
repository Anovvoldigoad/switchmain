#!/usr/bin/env python3
"""Configure explicit CPK paths/priorities; not a complete mod converter."""
import argparse,json
from pathlib import Path
from portlib.cpk_profile import encode,configure


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True,help='JSON array of path/priority objects')
    p.add_argument('--module',type=Path)
    p.add_argument('--expected-module-sha256')
    p.add_argument('--output',type=Path,required=True,help='New output directory')
    a=p.parse_args()
    if bool(a.module)!=bool(a.expected_module_sha256):
        p.error('--module and --expected-module-sha256 must be supplied together')
    rows=json.loads(a.manifest.read_text());profile=encode(rows)
    result=None;report={'entries':rows,'gameplay_verified':False,'full_moddingapi':False}
    if a.module:
        result,report['module']=configure(a.module.read_bytes(),profile,a.expected_module_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'cpk.profile').write_bytes(profile)
    (a.output/'cpk_profile_report.json').write_text(json.dumps(report,indent=2)+'\n')
    if result is not None:
        (a.output/'subsdk9.cpk_component_NOT_GAMEPLAY_RELEASE').write_bytes(result)
    print('Configured',len(rows),'CPK registrations; resource loading/gameplay not verified.')

if __name__=='__main__':main()
