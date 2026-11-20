#!/usr/bin/env python3
"""Mark explicit PC ModdingAPI PRMs inside an uncompressed CPK without rebuilding it.

The result is only the event-ownership conversion component of the port.
"""
import argparse,hashlib,json
from pathlib import Path
from portlib.cpk_events import mark


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cpk',type=Path,required=True)
    p.add_argument('--expected-sha256',required=True)
    p.add_argument('--pc-api-prm',action='append',required=True,help='Exact CPK path of a known PC API PRM; repeat for multiple PRMs')
    p.add_argument('--output',type=Path,required=True,help='New output directory; input is never overwritten')
    a=p.parse_args();data=a.cpk.read_bytes()
    if hashlib.sha256(data).hexdigest()!=a.expected_sha256.lower():
        p.error('Input CPK SHA256 mismatch')
    converted,report=mark(data,a.pc_api_prm)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/a.cpk.name).write_bytes(converted)
    (a.output/'cpk_event_marking_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CPK event markers integrated; other archive bytes unchanged. Not a complete gameplay package.')

if __name__=='__main__':main()
