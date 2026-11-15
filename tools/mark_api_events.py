#!/usr/bin/env python3
"""Mark a plaintext PC ModdingAPI PRM for the new Switch event dispatcher.

Only use a PRM known to require PC ModdingAPI. This does not port other assets.
"""
import argparse,json
from pathlib import Path
from portlib.prm_events import mark

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-api-prm',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True,help='New output directory')
    a=p.parse_args();data,report=mark(a.pc_api_prm.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/a.pc_api_prm.name).write_bytes(data)
    (a.output/'event_marking_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Marked {report["marked_records"]} events; {report["native_event236_preserved"]} native event236 records preserved. Not a gameplay package.')
if __name__=='__main__':main()
