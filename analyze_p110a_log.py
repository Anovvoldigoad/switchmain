#!/usr/bin/env python3
import re,sys
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit('usage: analyze_p110a_log.py <uzuy_log.txt>')
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
rows=[]; leader={}; paired={}
for line in lines:
    if '[NSC:P110A] MGR' in line:
        m=re.search(r'n=(\d+).*?ret=(\d+).*?phase=(\d+)->(\d+).*?team=(\d+)',line)
        if m: rows.append((int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),int(m.group(5)),line))
    elif '[NSC:P110A] LEADER' in line:
        m=re.search(r'n=(\d+).*?char=(\d+).*?action=(\d+)->(\d+).*?e94=(\d+)->(\d+).*?e9c=(\d+)->(\d+)',line)
        if m: leader[int(m.group(1))]=tuple(map(int,m.groups()[1:]))
    elif '[NSC:P110A] PAIRED' in line:
        m=re.search(r'n=(\d+).*?char=(\d+).*?action=(\d+)->(\d+).*?b968=(\d+)',line)
        if m: paired[int(m.group(1))]=tuple(map(int,m.groups()[1:]))
print('P110_ROWS',len(rows))
from collections import Counter
print('PHASE_TRANSITIONS',Counter((a,b) for _,_,a,b,_,_ in rows))
for n,ret,a,b,team,line in rows:
    l=leader.get(n); p=paired.get(n)
    if a in (1,2,3,4) or b!=a:
        print(f'n={n} phase={a}->{b} ret={ret} team={team} leader={l} paired={p}')
