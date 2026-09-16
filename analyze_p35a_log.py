#!/usr/bin/env python3
import collections, re, sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
t=p.read_text(errors='replace')
ready=[x for x in t.splitlines() if '[NSC:P35A] READY' in x]
events=[]
rx=re.compile(r'\[NSC:P35A\] EVT236 actor=(\S+) side=(\d+) char=(\d+) op=(-?\d+) p2=(-?\d+) p3=(-?\d+) p4bits=([0-9a-fA-F]+)')
for line in t.splitlines():
    m=rx.search(line)
    if m: events.append(tuple(m.groups()))
print('READY=', ready[-1] if ready else '<missing>')
print('event236_count=',len(events))
c=collections.Counter(int(e[3]) for e in events)
print('opcode_counts=',dict(sorted(c.items())))
print('\nEVENT236 TIMELINE')
for e in events:
    print(f'actor={e[0]} side={e[1]} char={e[2]} op={e[3]} p2={e[4]} p3={e[5]} p4bits={e[6]}')
print('\nFILE-LOAD FAILURES')
for line in t.splitlines():
    if '[NSC:P35A]' in line and (('FILE_OPEN' in line and 'result=0' in line) or 'status=5' in line or 'readerr=1' in line):
        print(line)
