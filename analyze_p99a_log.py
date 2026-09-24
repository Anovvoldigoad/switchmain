#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('uzuy_log.txt')
text=p.read_text(errors='replace')
ready=[l for l in text.splitlines() if '[NSC:P99A] READY' in l]
gates=[l for l in text.splitlines() if '[NSC:P99A] GATE1278' in l]
rx=re.compile(r'char=(\d+).*?ret=(\d+).*?action=(\d+)->(\d+).*?e94=(\d+)->(\d+).*?e9c=(\d+)->(\d+).*?f24=(\d+).*?q106f4=([0-9a-fA-F]+).*?q10f54=([0-9a-fA-F]+).*?q10f58=([0-9a-fA-F]+).*?q10f60=([0-9a-fA-F]+).*?q10f64=([0-9a-fA-F]+)')
rows=[]
for l in gates:
 m=rx.search(l)
 if m:
  rows.append(tuple(int(x,16) if i>=9 else int(x) for i,x in enumerate(m.groups())))
print('P99A_READY',len(ready),'GATE1278',len(gates),'PARSED',len(rows))
from collections import Counter,defaultdict
by=defaultdict(Counter)
for r in rows:
 cid,ret,a0,a1,e940,e941,e9c0,e9c1,f24,q0,q54,q58,q60,q64=r
 by[cid][(ret,a0,e940,e9c0,f24,q0,q54,q58,q60,q64)] += 1
for cid in sorted(by):
 print('CHAR',cid)
 for key,n in by[cid].most_common(20):
  print(' ',n,'ret/action/e94/e9c/f24/q0/q54/q58/q60/q64=',key)
print('DECISION_HINT: compare a successful vanilla UJ vs custom UJ. If custom action708 returns 1 while vanilla pre-710 returns 0, inspect the first differing raw dependency against static main+0x7EB518.')
