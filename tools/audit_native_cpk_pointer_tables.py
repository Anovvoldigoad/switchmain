#!/usr/bin/env python3
"""Inspect adjacent code relocation clusters in original SHA-pinned NSO main."""
import argparse
import json
from pathlib import Path
from portlib.native_cpk_pointer_tables import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True,help='New report directory')
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'native_cpk_pointer_candidates.json').write_text(json.dumps(report,indent=2)+'\n')
    for group in report['clusters'][:6]:
        print('CPK_CODE_POINTER_GROUP',group['first_slot'],
              'relocated_slots',group['contiguous_relocated_slot_count'],
              'head_members',group['reported_members'][:9],
              'is_vtable_unproven=1')
    print('Static relocation groups only; no ABI, async lifecycle or gameplay proof.')


if __name__=='__main__':main()
