#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
text=p.read_text(errors='replace')
ready=re.findall(r'^.*\[NSC:P115B\] READY.*$',text,re.M)
rows=re.findall(r'^.*\[NSC:P115B\] EVT_GATE.*$',text,re.M)
print('P115B_READY',len(ready))
if ready: print(ready[-1])
print('EVT_GATE_ROWS',len(rows))
for r in rows: print(r)
custom=[r for r in rows if 'char=281 ' in r]
vanilla=[r for r in rows if 'char=281 ' not in r]
print('CUSTOM_ROWS',len(custom),'VANILLA_OR_OTHER_ROWS',len(vanilla))
if custom:
    vals=[]
    for r in custom:
        m=re.search(r'raw_type=(\d+) norm_type=(\d+) pass=(\d+)',r)
        if m: vals.append(tuple(map(int,m.groups())))
    print('CUSTOM_EVENT_VALUES',vals)
    if any(v[2]==0 for v in vals): print('DECISION=CUSTOM_REACHES_EVENT_GATE_BUT_TYPE_NOT_10_11')
    elif any(v[2]==1 for v in vals): print('DECISION=CUSTOM_REACHES_AND_PASSES_EVENT_GATE_NEXT_PROBE_ACTOR_C48_ONLY')
else:
    print('DECISION=CUSTOM_NEVER_REACHES_77C474_BACKSLICE_EVENT_DISPATCH_UPSTREAM')
