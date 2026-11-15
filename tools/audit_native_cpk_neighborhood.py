#!/usr/bin/env python3
"""Read-only native CPK near-anchor target and indirect branch census."""
import argparse
import json
from pathlib import Path
from portlib.native_cpk_neighborhood import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--main',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path,help='New directory')
    a=p.parse_args()
    result=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'native_cpk_neighborhood.json').write_text(json.dumps(result,indent=2)+'\n')
    for w in result['regions']:
        print('NATIVE_NEARBY',w['name'],'incoming',w['incoming_counts'],
              'targets',w['common_nearby_direct_targets'][:8],
              'indirect_branch_count',w['nearby_indirect_branch_count'],
              'reloc_addend_count',w['relative_relocation_addend_count'],
              'no_lifecycle_proof=1')


if __name__=='__main__':main()
