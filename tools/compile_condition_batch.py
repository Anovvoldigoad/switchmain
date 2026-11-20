#!/usr/bin/env python3
"""Compile multiple explicit CPK components; NOT a gameplay release."""
import argparse,json
from pathlib import Path
from portlib.condition_batch import build


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True,
                   help='JSON: condition_owner, archives[{source,sha256,path,priority,pc_api_prms}]')
    p.add_argument('--pc-manager',type=Path,required=True)
    p.add_argument('--expected-manager-sha256',required=True)
    p.add_argument('--module',type=Path)
    p.add_argument('--expected-module-sha256')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    report=build(json.loads(a.manifest.read_text()),a.pc_manager.read_bytes(),
                 a.expected_manager_sha256,a.output,
                 a.module.read_bytes() if a.module is not None else None,
                 a.expected_module_sha256)
    print('Component batch:',report['archive_count'],'CPKs. Native precedence and gameplay unverified.')


if __name__=='__main__':main()
