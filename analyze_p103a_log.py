#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=2:
    raise SystemExit('usage: analyze_p103a_log.py <uzuy_log.txt>')
text=Path(sys.argv[1]).read_text(errors='replace')
lines=text.splitlines()
ready=[x for x in lines if '[NSC:P103A] READY' in x]
remap=[x for x in lines if '[NSC:P103A] REMAP' in x]
print('P103A_READY_COUNT',len(ready))
for x in ready[-3:]: print(x)
print('P103A_REMAP_COUNT',len(remap))
rx=re.compile(r'selector=(\d+) mapped=(\d+) context=(\d+) ret=(\S+)')
for x in remap[:100]:
    m=rx.search(x)
    if m: print('REMAP selector=%s mapped=%s context=%s ret=%s'%m.groups())
    else: print(x)
# Existing parent-chain evidence useful for the one-run decision.
keys=('index=710','requested=710','post_action=710',' 708 -> 710','action=710','P91A','P96A','EVT121_SELF','SW_MTOB_XH')
hits=[]
for x in lines:
    if any(k in x for k in keys): hits.append(x)
print('RELEVANT_PARENT_LINES',len(hits))
for x in hits[-220:]: print(x)
