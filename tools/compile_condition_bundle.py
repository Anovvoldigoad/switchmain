#!/usr/bin/env python3
"""Bind one CPK's actual condition companion to descriptor and CPK profiles.

Output is a review component bundle; raw values and game lifecycle remain unverified.
"""
import argparse,json
from pathlib import Path
from portlib.condition_bundle import compile_bundle,configure_module
from portlib.cpk_profile import PREFIX


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--param',type=Path,required=True)
    p.add_argument('--cpk',type=Path,required=True)
    p.add_argument('--expected-cpk-sha256',required=True)
    p.add_argument('--runtime-path',required=True)
    p.add_argument('--priority',type=int,required=True)
    p.add_argument('--pc-api-prm',action='append',default=[],help='Exact known PC ModdingAPI PRM path; no automatic guessing')
    p.add_argument('--module',type=Path)
    p.add_argument('--expected-module-sha256')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if bool(a.module)!=bool(a.expected_module_sha256):p.error('Module and hash must be supplied together')
    archive,condition,registration,report=compile_bundle(a.param.read_bytes(),a.cpk.read_bytes(),a.expected_cpk_sha256,a.runtime_path,a.priority,a.pc_api_prm)
    module=None
    if a.module:module,report['module']=configure_module(a.module.read_bytes(),a.expected_module_sha256,condition,registration)
    # Validate the complete inputs before any output directory is created.
    a.output.mkdir(parents=True,exist_ok=False)
    target=a.output/'component_data'/a.runtime_path[len(PREFIX):]
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive)
    report['archive_relative_path']=target.relative_to(a.output).as_posix()
    (a.output/'condition.profile').write_bytes(condition)
    (a.output/'cpk.profile').write_bytes(registration)
    if module is not None:(a.output/'subsdk9.COMPONENT_NOT_GAMEPLAY_RELEASE').write_bytes(module)
    (a.output/'condition_bundle_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Condition/archive/profile component bundle written; NOT a gameplay installation package.')

if __name__=='__main__':main()
