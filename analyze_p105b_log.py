#!/usr/bin/env python3
import re,sys
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit('usage: python3 analyze_p105b_log.py <uzuy_log.txt>')
p=Path(sys.argv[1]); lines=p.read_text(errors='replace').splitlines()
ready=[x for x in lines if '[NSC:P105B] READY' in x]
ctrl=[x for x in lines if '[NSC:P105B] CTRL4C0' in x]
state=[x for x in lines if '[NSC:P105B] STATE4C0' in x]
play=[]
for x in lines:
    if '[NSC:P59A] PLAY_CALL' not in x: continue
    m=re.search(r'caller_off=0x([0-9a-fA-F]+)',x)
    if not m: continue
    off=int(m.group(1),16)
    if off in (0x7DE558,0x7E6EC8): play.append(x)
print('P105B_READY',len(ready))
for x in ready[:3]: print(x)
print('P105B_CTRL4C0_ROWS',len(ctrl))
for x in ctrl: print(x)
print('P105B_STATE4C0_ROWS',len(state))
for x in state: print(x)
print('PRODUCER_PLAY_CALLS',len(play))
for x in play: print(x)
if not ready:
    print('VERDICT: P105B did not reach READY; inspect hook install/boot failure.')
elif not ctrl:
    print('VERDICT: no focused +0x4C0 sample; successful/failing action corridor may not have invoked +0x4C0 while focused.')
else:
    modes=[]
    for x in ctrl:
        m=re.search(r'phase=0.*?mode=(\d+)',x)
        if m: modes.append(int(m.group(1)))
    print('CTRL4C0_ENTER_MODES',modes)
    print('VERDICT: correlate CTRL4C0/STATE4C0 pairs by seq+phase with P59 caller 0x7DE558 (261). Caller 0x7E6EC8 is native +0x520 -> 710 control evidence.')
