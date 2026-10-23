#!/usr/bin/env python3
"""P33: classify P32 loader events per observed attempt, never per path lifetime.

An attempt is a PROCESS observation and preceding FILE_OPEN observations for the
same path since the previous PROCESS. This is temporal correlation, NOT proof
of identical native request pointers (FILE_OPEN.request != PROCESS.owner).
When events cannot be paired, report UNCORRELATED rather than inventing cause.
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

PATH = re.compile(r"\\bpath=(.*?) (?=(?:slot=|owner=|first=))")
OPEN = re.compile(r"\\bslot=(\\d+) result=(\\d+)")
PROC = re.compile(r"\\bstatus=(\\d+) readerr=(\\d+)")
STATUS = re.compile(r"\\bstatus=(\\d+)(?:\\s|$)")
def parse(lines):
    events=[]
    for number,line in enumerate(lines,1):
        if "[NSC:P32]" not in line: continue
        kind=next((k for k in ("FILE_OPEN","PROCESS","LOAD_STATUS") if " "+k+" " in line),None)
        if kind is None: continue
        match=PATH.search(line)
        if match is None: continue
        path=match.group(1)
        fields=(OPEN if kind=="FILE_OPEN" else PROC if kind=="PROCESS" else STATUS).search(line)
        if not fields: continue
        e={"line":number,"kind":kind,"path":path}
        if kind=="FILE_OPEN": e.update(slot=int(fields[1]),open_result=int(fields[2]))
        elif kind=="PROCESS": e.update(status=int(fields[1]),readerr=int(fields[2]))
        else: e.update(status=int(fields[1]))
        events.append(e)
    return events

def classify(events):
    pending=defaultdict(list)
    attempts=[]
    orphan_status=[]
    for e in events:
        path=e["path"]
        if e["kind"]=="FILE_OPEN":
            pending[path].append(e)
        elif e["kind"]=="PROCESS":
            opens=pending.pop(path,[])
            values={x["open_result"] for x in opens}
            # A PROCESS is an observation, not necessarily the terminal state.
            if not opens: cause="UNCORRELATED_NO_OPEN"
            elif len(values)>1: cause="AMBIGUOUS_MULTIPLE_OPENS"
            elif e["status"]==5 and values=={0}: cause="OPEN_FAIL_OBSERVED"
            elif e["status"]==5 and values=={1} and e["readerr"]==1:
                cause="XFBIN_READ_FAIL_OBSERVED"
            elif e["status"]==5: cause="STATUS5_OTHER_OR_UNKNOWN"
            elif e["status"]==2 and values=={1}: cause="LOAD_SUCCESS_OBSERVED"
            else: cause="INCOMPLETE_OR_OTHER"
            attempts.append({"path":path,"process_line":e["line"],
                             "status":e["status"],"readerr":e["readerr"],
                             "open_lines":[x["line"] for x in opens],
                             "open_results":[x["open_result"] for x in opens],
                             "classification":cause})
        else: orphan_status.append(e)
    return {"attempts":attempts,
            "unpaired_opens":[e for arr in pending.values() for e in arr],
            "status_events":orphan_status,
            "caveat":"Temporal path correlation only. Concurrent or nested same-path requests cannot be definitively matched without native request IDs."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("log",type=Path)
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()
    report=classify(parse(args.log.read_text(errors="replace").splitlines()))
    if args.json:
        print(json.dumps(report,indent=2))
    else:
        for a in report["attempts"]:
            print(f'{a["classification"]} path={a["path"]} status={a["status"]} readerr={a["readerr"]} process_line={a["process_line"]} open_lines={a["open_lines"]}')
        print("UNPAIRED_OPEN",len(report["unpaired_opens"]))
        print(report["caveat"])
if __name__=="__main__": main()
