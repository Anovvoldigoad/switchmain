#!/usr/bin/env python3
"""Read-only pinned main relocation + immediate address references near CPK anchors."""
import argparse,json
from pathlib import Path
from portlib.native_cpk_indirect import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True,help='New directory')
    a=p.parse_args()
    result=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'native_cpk_indirect_refs.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in result['anchors']:
        materializations=row['direct_code_address_materializations']
        loads=row['load_relocation_slot_candidates']
        print('NSC_INDIRECT_CANDIDATE',row['name'],
              'reloc_slots',row['relative_relocation_slots'][:8],
              'adr',materializations['adr'][:8],
              'adrp_add',materializations['immediately_adjacent_adrp_add'][:8],
              'adrp_ldr',loads['immediately_adjacent_adrp_ldr'][:8],
              'literal_ldr',loads['literal_ldr'][:8])
    print('STATIC only; no CRI async, unbind or gameplay proof.')


if __name__=='__main__':
    main()
