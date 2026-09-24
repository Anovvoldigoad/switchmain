#!/usr/bin/env python3
from pathlib import Path
import re, sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
text=p.read_text(errors='replace')
lines=text.splitlines()
ready=[x for x in lines if '[NSC:P95A] READY' in x]
queue=[x for x in lines if '[NSC:P95A] QUEUECTRL' in x]
wrap=[x for x in lines if '[NSC:P95A] WRAPPER_PARENT' in x]
print('P95A_READY', len(ready))
print('QUEUECTRL', len(queue), 'WRAPPER_PARENT', len(wrap))

def field(line,name,base=10):
    m=re.search(rf'\b{re.escape(name)}=([0-9a-fA-Fx-]+)',line)
    if not m:return None
    s=m.group(1)
    try:return int(s,0 if s.startswith(('0x','-0x')) else base)
    except:return None

def hexfield(line,name):
    m=re.search(rf'\b{re.escape(name)}=([0-9a-fA-F]{{8}})',line)
    return int(m.group(1),16) if m else None

interesting=[]
for x in queue:
    code=field(x,'code'); action=field(x,'action'); caller=re.search(r'caller_off=0x([0-9a-fA-F]+)',x)
    q=hexfield(x,'q10600'); q2=hexfield(x,'q105fc')
    if code in (707,708,710) or action in (707,708) or (caller and int(caller.group(1),16)==0x7725d0):
        interesting.append((x,q,q2))
print('\nDECISIVE_QUEUE_SNAPSHOTS')
for x,q,q2 in interesting[-80:]:
    print(x)

print('\nWRAPPER_PARENT_SUMMARY')
for x in wrap:
    idx=field(x,'index')
    h48=field(x,'hit48fe4'); h77=field(x,'hit7732a8'); h7e=field(x,'hit7eff8c')
    q=hexfield(x,'q10600'); q2=hexfield(x,'q105fc')
    eb=re.search(r'\beb0calls=(\d+)',x)
    print(f'index={idx} q10600={q} q105fc={q2} hit48fe4={h48} hit7732a8={h77} hit7eff8c={h7e} eb0calls={eb.group(1) if eb else "?"}')
    print(x)

if wrap:
    decisive=[x for x in wrap if field(x,'index')==708]
    if decisive:
        print('\nP95A_708_DECISION')
        for x in decisive:
            q=hexfield(x,'q10600'); q2=hexfield(x,'q105fc')
            h48=field(x,'hit48fe4'); h77=field(x,'hit7732a8'); h7e=field(x,'hit7eff8c')
            if h77:
                print('708 parent includes 0x7732A8 (vtable+EB0 path loading actor+0x10600). q10600=',q)
            elif h7e:
                print('708 parent includes 0x7EFF8C (alternate vtable+EB0 path; W1 comes from helper result). q10600=',q)
            elif h48:
                print('708 parent includes 0x48FE4 (direct 0x48F18 sequence path). q10600=',q)
            else:
                print('708 parent not one of three named parents; inspect e0..e5/c0..c7 stack return candidates.')
else:
    print('\nNo P95A wrapper provenance lines found.')
