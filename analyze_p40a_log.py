#!/usr/bin/env python3
import re,sys
from collections import Counter,defaultdict
p=sys.argv[1]
lines=open(p,encoding='utf-8',errors='replace').read().splitlines()
markers=['READY','CTRL14_DIRECT','EVT13_AWAKE','EVT121_COND','OUGI_CORE','EVT236','EVT235_SHOW','STAGE_HANDLE','FIX_CHAR','POST_STAGE','FILE_OPEN','PROCESS']
print('P40A log:',p)
for m in markers:
    print(f'{m:16} {sum(("[NSC:P40A] "+m) in x for x in lines)}')
print('fingerprint_FAIL',sum('[NSC:P40A] fingerprint FAIL' in x for x in lines))
print('custom_FILE_OPEN_result0',sum('[NSC:P40A] FILE_OPEN' in x and 'result=0' in x for x in lines))
print('PROCESS_status5',sum('[NSC:P40A] PROCESS' in x and 'status=5' in x for x in lines))
print('PROCESS_readerr1',sum('[NSC:P40A] PROCESS' in x and 'readerr=1' in x for x in lines))
sel=Counter(); wrote=Counter(); evtops=Counter(); cond=Counter(); modes=Counter()
for x in lines:
    if '[NSC:P40A] CTRL14_DIRECT' in x:
        m=re.search(r'p3=(-?\d+).*old=(-?\d+).*wrote=(\d+)',x)
        if m:
            sel[int(m.group(1))]+=1; wrote[(int(m.group(2)),int(m.group(3)))]+=1
    if '[NSC:P40A] EVT236' in x:
        m=re.search(r'op=(-?\d+)',x)
        if m: evtops[int(m.group(1))]+=1
    if '[NSC:P40A] EVT121_COND' in x:
        m=re.search(r'text=([^ ]*)',x)
        if m: cond[m.group(1)]+=1
    if '[NSC:P40A] OUGI_CORE' in x:
        m=re.search(r'mode=(\d+)',x)
        if m: modes[int(m.group(1))]+=1
print('CTRL14 selectors:',dict(sorted(sel.items())))
print('CTRL14 old,wrote:',dict(sorted(wrote.items())))
print('EVT236 opcodes:',dict(sorted(evtops.items())))
print('EVT121 names:',dict(cond))
print('OUGI modes:',dict(sorted(modes.items())))
print('\n--- focused state trace ---')
for x in lines:
    if any(k in x for k in ('EVT13_AWAKE','EVT121_COND','OUGI_CORE')):
        print(x)
