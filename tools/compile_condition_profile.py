#!/usr/bin/env python3
"""Compile a merged PC conditionprmManager table; not a complete gameplay package."""
import argparse,json
from pathlib import Path
from portlib.condition_profile import compile_table,configure

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--param',type=Path,required=True,help='Raw merged NSC PC conditionprmManager.xfbin (112-byte rows)')
    p.add_argument('--module',type=Path);p.add_argument('--expected-module-sha256')
    p.add_argument('--output',type=Path,required=True,help='New output directory')
    a=p.parse_args()
    if bool(a.module)!=bool(a.expected_module_sha256):p.error('Module and its expected hash must be provided together')
    profile,report=compile_table(a.param.read_bytes());result=None
    if a.module:result,report['module']=configure(a.module.read_bytes(),profile,a.expected_module_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'condition.profile').write_bytes(profile)
    (a.output/'condition_profile_report.json').write_text(json.dumps(report,indent=2)+'\n')
    if result is not None:(a.output/'subsdk9.condition_component_NOT_GAMEPLAY_RELEASE').write_bytes(result)
    print('Compiled',report['appended_descriptors'],'descriptors; separate raw condition data and gameplay remain unverified.')
if __name__=='__main__':main()
