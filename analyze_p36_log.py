#!/usr/bin/env python3
import re, sys, collections
from pathlib import Path
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('uzuy_log.txt')
lines=p.read_text(errors='replace').splitlines()
time_re=re.compile(r'^\[\s*([0-9.]+)\]')
mark='[NSC:P36]'
rows=[]
for i,line in enumerate(lines,1):
    if mark not in line: continue
    m=time_re.search(line); t=float(m.group(1)) if m else -1.0
    msg=line.split(mark,1)[1].strip()
    rows.append((t,i,msg))
print(f'P36 markers={len(rows)}')
counts=collections.Counter()
actors=collections.Counter()
ops=collections.Counter()
for t,i,msg in rows:
    kind=msg.split()[0] if msg else '<empty>'
    counts[kind]+=1
    ma=re.search(r'actor=(0x[0-9a-fA-F]+)',msg)
    if ma: actors[ma.group(1)]+=1
    mo=re.search(r'\bop=(-?\d+)',msg)
    if mo: ops[int(mo.group(1))]+=1
print('kinds:',dict(counts))
print('actors:',dict(actors))
print('ops:',dict(sorted(ops.items())))
print('\n--- lifecycle timeline ---')
for t,i,msg in rows:
    if msg.startswith(('STAGE_HANDLE','FIX_CHAR','POST_STAGE','EVT235_SHOW','EVT236','ACTION')):
        print(f'{t:10.6f} L{i}: {msg}')
