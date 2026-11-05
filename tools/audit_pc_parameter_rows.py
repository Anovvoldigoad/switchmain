#!/usr/bin/env python3
"""Inspect SHA-pinned PC SusanooCond/PartnerSlot raw32 parameters (NOT Switch loader)."""
import argparse,json
from pathlib import Path
from portlib.pc_param_rows import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--family',choices=['susanooCondParam','partnerSlotParam'],required=True)
    p.add_argument('--input',type=Path,required=True,
                   help='Extracted PC raw32 payload, NOT a NUCC XFBIN container')
    p.add_argument('--expected-sha256',required=True)
    p.add_argument('--output',type=Path,required=True,help='New output directory')
    a=p.parse_args()
    report=inspect(a.input.read_bytes(),a.family,a.expected_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'pc_parameter_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PC source-format validation only:',a.family,report['record_count'],
          'rows; no native Switch runtime or gameplay proof.')


if __name__=='__main__':
    main()
