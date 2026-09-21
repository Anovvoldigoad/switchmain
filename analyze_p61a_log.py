#!/usr/bin/env python3
from pathlib import Path
import re,sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
text=p.read_text(errors='replace')
lines=text.splitlines()
ready=[l for l in lines if '[NSC:P61A] READY' in l]
gates=[]
plays=[]
for i,l in enumerate(lines):
    if '[NSC:P61A] UJ_GATE_COMPAT' in l:
        m=re.search(r'char=(\d+).*?orig=(\d+).*?override=(\d+).*?caller_off=0x([0-9a-fA-F]+).*?native_slot8=(\d+)',l)
        if m:
            gates.append((i,*map(lambda x:int(x,16) if x.startswith('0x') else int(x), [])))
            gates[-1:]=[(i,int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4),16),int(m.group(5)),l)]
    if '[NSC:P59A] PLAY_CALL' in l:
        m=re.search(r'char=(\d+) index=(-?\d+)',l)
        if m: plays.append((i,int(m.group(1)),int(m.group(2)),l))
custom_gates=[g for g in gates if 281 <= g[1] < 0x1000 and g[2]==0 and g[3]==1 and g[4]==0xC7874 and g[5]==1]
custom700=[x for x in plays if 281 <= x[1] < 0x1000 and x[2]==700]
custom445=[x for x in plays if 281 <= x[1] < 0x1000 and x[2]==445]
linked=[]
for g in custom_gates:
    later=[x for x in custom700 if x[0] >= g[0] and x[0]-g[0] <= 300]
    if later: linked.append((g,later[0]))
print(f'P61A_READY={1 if ready else 0}')
print(f'P61A_GUARDED_OVERRIDES={len(custom_gates)}')
print(f'CUSTOM_PLAY700={len(custom700)}')
print(f'CUSTOM_PLAY445={len(custom445)}')
for g in custom_gates[:8]:
    print(f'GATE char={g[1]} orig={g[2]} override={g[3]} caller_off=0x{g[4]:x} slot8={g[5]}')
for x in custom700[:8]: print(f'PLAY700 char={x[1]} line={x[0]+1}')
if linked:
    print('P61A_RESULT=PASS_GUARDED_GATE_REACHED_CUSTOM_UJ700')
elif custom_gates:
    print('P61A_RESULT=PARTIAL_GATE_OVERRIDE_BUT_NO_CUSTOM_UJ700')
elif ready:
    print('P61A_RESULT=NO_GATE_OVERRIDE_OBSERVED')
else:
    print('P61A_RESULT=BUILD_NOT_ACTIVE')
