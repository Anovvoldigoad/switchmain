#!/usr/bin/env python3
import re, sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
text=p.read_text(errors='replace')
lines=[ln for ln in text.splitlines() if '[NSC:P29]' in ln]
for ln in lines: print(ln)
mt=[ln for ln in lines if 'mtob' in ln.lower() and 'prm_load' in ln.lower()]
print('\n=== P29 SUMMARY ===')
print('p29_lines=',len(lines))
print('mtob_prm_lines=',len(mt))
req=[x for x in mt if 'LOAD_REQ' in x]
cre=[x for x in mt if 'LOAD_CREATE' in x]
sta=[x for x in mt if 'LOAD_STATUS' in x]
print('LOAD_REQ=',len(req),'LOAD_CREATE=',len(cre),'LOAD_STATUS=',len(sta))
statuses=[]
for x in sta:
    m=re.search(r'status=(\d+)',x)
    if m: statuses.append(int(m.group(1)))
print('statuses=',statuses)
if not req:
    print('CLASS=A: mtobprm_load never reached nuccFileLoad request hook.')
elif req and not cre:
    print('CLASS=B: request exists but no fresh create call; path likely reused/found in nuccFileLoadList.')
elif cre:
    print('CLASS=C: fresh load object creation was attempted for mtobprm_load.')
if 4 in statuses:
    print('STATUS4: 0x1207EFC did not find the path in nuccFileLoadList at status query time.')
if 5 in statuses:
    print('STATUS5: native nuccFileLoad::IsLoaded error state observed.')
if 2 in statuses:
    print('STATUS2: native IsLoaded condition is satisfied; if preview still fails, move downstream to prm_load parsing/resource rows.')
