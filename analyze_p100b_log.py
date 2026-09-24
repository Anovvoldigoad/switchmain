#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1]); lines=p.read_text(errors='replace').splitlines()
route=[x for x in lines if '[NSC:P100B] ROUTE' in x]
ready=[x for x in lines if '[NSC:P100B] READY' in x]
print('ready',len(ready),'route',len(route))
for cid in (91,281):
 xs=[x for x in route if f'char={cid} ' in x]
 print('\nCHAR',cid,'count',len(xs))
 last=None
 for x in xs:
  m=re.search(r'stage=([^ ]+)',x); st=m.group(1) if m else '?'
  if st!=last or st in ('REQUEST710_7E6EA8','REMAPRET_7E6C50'):
   print(x)
  last=st
print('\nCUSTOM_REQUEST710',sum('char=281 ' in x and 'stage=REQUEST710_7E6EA8' in x for x in route))
print('VANILLA_REQUEST710',sum('char=91 ' in x and 'stage=REQUEST710_7E6EA8' in x for x in route))
