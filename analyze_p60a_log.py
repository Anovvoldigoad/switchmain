#!/usr/bin/env python3
import re,sys
from pathlib import Path

if len(sys.argv)!=2:
    raise SystemExit('usage: analyze_p60a_log.py <uzuy_log.txt>')
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
port=[]; play=[]; setter=[]
for line in lines:
    if '[NSC:P60A] CTRL14_UJ_PORT ' in line:
        m=re.search(r'char=(\d+).*?before=(-?\d+).*?after=(-?\d+)',line)
        if m: port.append((int(m.group(1)),int(m.group(2)),int(m.group(3)),line))
    if '[NSC:P59A] PLAY_CALL ' in line:
        m=re.search(r'char=(\d+).*?index=(\d+).*?pre=(\d+).*?post=(\d+)',line)
        if m: play.append((int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),line))
    if '[NSC:P57A] SETTER ' in line:
        m=re.search(r'char=(\d+).*?requested=(\d+).*?e94=(-?\d+)->(-?\d+)',line)
        if m: setter.append((int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),line))

custom_ids=sorted({c for c,_,_,_ in port if c>=281} | {c for c,_,_,_,_ in play if c>=281})
print(f'P60A_PORT_EVENTS={len(port)}')
for c,b,a,_ in port:
    print(f'PORT char={c} slot8={b}->{a}')

for c in custom_ids:
    acts=[idx for cc,idx,_,_,_ in play if cc==c]
    e94_700=[(a,b) for cc,req,a,b,_ in setter if cc==c and req==700]
    print(f'CUSTOM char={c} play_indices={acts}')
    print(f'CUSTOM char={c} has_445={int(445 in acts)} has_700={int(700 in acts)} setter700_e94={e94_700}')

port_after_ok=any(c>=281 and a!=0 for c,_,a,_ in port)
custom_700=any(c>=281 and idx==700 for c,idx,_,_,_ in play)
custom_445=any(c>=281 and idx==445 for c,idx,_,_,_ in play)
if port_after_ok and custom_700:
    print('P60A_ROOT_PORT_RESULT=PASS_CUSTOM_REACHED_UJ700')
elif port_after_ok and custom_445:
    print('P60A_ROOT_PORT_RESULT=PARTIAL_SLOT8_ENABLED_BUT_CUSTOM_STILL_445')
elif not port:
    print('P60A_ROOT_PORT_RESULT=NO_PORT_EVENT_SEEN')
else:
    print('P60A_ROOT_PORT_RESULT=INCONCLUSIVE')
