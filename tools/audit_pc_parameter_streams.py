#!/usr/bin/env python3
"""Review raw PC Ougi/Gudo/CharRelation streams without touching Switch runtime."""
import argparse
import json
from pathlib import Path
from portlib.pc_param_streams import inspect, SOURCE


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--family',required=True,choices=sorted(SOURCE))
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--expected-sha256',required=True)
    p.add_argument('--output',required=True,type=Path,help='New report directory')
    a=p.parse_args()
    report=inspect(a.input.read_bytes(),a.family,a.expected_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'pc_parameter_stream_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Validated raw PC format only:',a.family,report['record_count'],
          'records. No Switch integration or gameplay proven.')


if __name__=='__main__':main()
