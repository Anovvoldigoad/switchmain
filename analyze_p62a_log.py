#!/usr/bin/env python3
from pathlib import Path
import re,sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
lines=p.read_text(errors='replace').splitlines()
ready=[]; persist=[]; source_ports=[]; plays=[]
for i,l in enumerate(lines):
    if '[NSC:P62A] READY' in l: ready.append((i,l))
    if '[NSC:P62A] CTRL_GET_UJ_PERSIST' in l:
        m=re.search(r'char=(\d+).*?selector=(-?\d+).*?raw=(-?\d+).*?returned=(\d+).*?caller_off=0x([0-9a-fA-F]+)',l)
        if m: persist.append((i,int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),int(m.group(5),16),l))
    if '[NSC:P60A] CTRL14_UJ_PORT' in l:
        m=re.search(r'char=(\d+).*?native_selector=(\d+).*?before=(-?\d+).*?after=(-?\d+)',l)
        if m: source_ports.append((i,int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),l))
    if '[NSC:P59A] PLAY_CALL' in l:
        m=re.search(r'char=(\d+) index=(-?\d+)',l)
        if m: plays.append((i,int(m.group(1)),int(m.group(2)),l))
custom_persist=[x for x in persist if 281 <= x[1] < 0x1000 and x[2]==8 and x[3]==0 and x[4]==1]
router_persist=[x for x in custom_persist if x[5] in (0xC7934,0xC79B0)]
custom700=[x for x in plays if 281 <= x[1] < 0x1000 and x[2]==700]
custom445=[x for x in plays if 281 <= x[1] < 0x1000 and x[2]==445]
custom_source=[x for x in source_ports if 281 <= x[1] < 0x1000 and x[2]==8 and x[4]!=0]
linked=[]
for g in custom_persist:
    later=[x for x in custom700 if x[0]>=g[0] and x[0]-g[0] <= 350]
    if later: linked.append((g,later[0]))
print(f'P62A_READY={1 if ready else 0}')
print(f'CUSTOM_SOURCE_UJ_ENABLE_EVENTS={len(custom_source)}')
print(f'P62A_PERSISTENT_GETTER_OVERRIDES={len(custom_persist)}')
print(f'P62A_UJ_ROUTER_GETTER_OVERRIDES={len(router_persist)}')
print(f'CUSTOM_PLAY700={len(custom700)}')
print(f'CUSTOM_PLAY445={len(custom445)}')
for x in custom_persist[:12]: print(f'PERSIST char={x[1]} selector={x[2]} raw={x[3]} returned={x[4]} caller_off=0x{x[5]:x} line={x[0]+1}')
for x in custom700[:8]: print(f'PLAY700 char={x[1]} line={x[0]+1}')
if not ready:
    print('P62A_RESULT=BUILD_NOT_ACTIVE')
elif linked:
    print('P62A_RESULT=PASS_PERSISTENT_CONTROL_REACHED_CUSTOM_UJ700')
elif router_persist:
    print('P62A_RESULT=PARTIAL_UJ_ROUTER_SAW_PERSISTENT_SLOT8_BUT_NO_CUSTOM700')
elif custom_persist:
    print('P62A_RESULT=PARTIAL_PERSISTENCE_ACTIVE_OUTSIDE_KNOWN_UJ_ROUTER_NO_CUSTOM700')
elif custom_source:
    print('P62A_RESULT=UPSTREAM_ROUTE_NEVER_QUERIED_PERSISTENT_UJ_SELECTOR8')
else:
    print('P62A_RESULT=NO_SOURCE_UJ_ENABLE_OBSERVED')
