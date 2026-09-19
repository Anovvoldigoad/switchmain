#!/usr/bin/env python3
import re, sys, collections
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit('usage: analyze_p57a_log.py uzuy_log.txt')
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
ready=[x for x in lines if '[NSC:P57A] READY' in x]
rows=[]
pat=re.compile(r'\[NSC:P57A\] SETTER .*?char=(\d+) requested=(-?\d+) a2=(-?\d+) a3=(-?\d+) pre=(\d+) post=(\d+).*?caller_main=(\d+) caller_off=0x([0-9a-fA-F]+)')
for x in lines:
    m=pat.search(x)
    if m:
        rows.append(tuple(int(v,16) if i==7 else int(v) for i,v in enumerate(m.groups())))
print('P57A_ANALYSIS')
print('READY',len(ready))
print('SETTER_ROWS',len(rows))
bychar=collections.Counter(r[0] for r in rows)
print('BY_CHAR',dict(sorted(bychar.items())))
custom=[r for r in rows if 280 < r[0] < 0x1000]
print('CUSTOM_ROWS',len(custom))
byreq=collections.Counter((r[1],r[6],r[7]) for r in custom)
print('CUSTOM requested/caller_main/caller_off counts:')
for k,n in byreq.most_common():
    print(f'  action={k[0]} caller_main={k[1]} caller_off=0x{k[2]:x} count={n}')
print('CUSTOM sequence:')
for r in custom:
    print(f'  char={r[0]} requested={r[1]} a2={r[2]} a3={r[3]} pre={r[4]} post={r[5]} caller_main={r[6]} caller_off=0x{r[7]:x}')
