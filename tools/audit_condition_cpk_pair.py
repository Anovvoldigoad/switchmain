#!/usr/bin/env python3
"""Audit condition raw values embedded in two exact-identity CPK files."""
import argparse
import json
from pathlib import Path
from portlib.condition_archive_audit import inspect


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-manager',type=Path,required=True)
    p.add_argument('--stock-cpk',type=Path,required=True)
    p.add_argument('--stock-cpk-sha256',required=True)
    p.add_argument('--candidate-cpk',type=Path,required=True)
    p.add_argument('--candidate-cpk-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    report=inspect(a.pc_manager.read_bytes(),a.stock_cpk,a.stock_cpk_sha256,
                   a.candidate_cpk,a.candidate_cpk_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'condition_cpk_pair_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CPK condition raw comparison completed; origin and gameplay unverified.')


if __name__=='__main__':
    main()
