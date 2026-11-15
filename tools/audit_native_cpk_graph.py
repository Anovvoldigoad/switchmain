#!/usr/bin/env python3
"""Extract pinned v1.70 native CPK/file-load direct-branch candidates, read-only."""
import argparse,json
from pathlib import Path
from portlib.native_cpk_graph import analyze


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    report=analyze(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'native_cpk_call_edges.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in report['anchors']:
        print(r['name'],r['offset'],'incoming_candidate_edges',r['incoming_count'],
              'bounded_outgoing_edges',len(r['outgoing_edges_in_bounded_window']))
    print('Read-only static census. Async completion/unbind and gameplay NOT proven.')


if __name__=='__main__':main()
