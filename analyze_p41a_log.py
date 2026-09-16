#!/usr/bin/env python3
import re,sys
from collections import Counter
p=sys.argv[1]
lines=open(p,encoding='utf-8',errors='replace').read().splitlines()
markers=['READY','CTRL14_SHADOW','EVT13_RAW','EVT13_AWAKE','EVT121_SELF','EVT121_NATIVE','OUGI_RAW','OUGI_CORE','EVT236','EVT235_SHOW','STAGE_HANDLE','FIX_CHAR','POST_STAGE','FILE_OPEN','PROCESS']
print('P41A log:',p)
for m in markers:
    print(f'{m:16} {sum(("[NSC:P41A] "+m) in x for x in lines)}')
print('fingerprint_FAIL',sum('[NSC:P41A] fingerprint FAIL' in x for x in lines))
print('custom_FILE_OPEN_result0',sum('[NSC:P41A] FILE_OPEN' in x and 'result=0' in x for x in lines))
print('PROCESS_status5',sum('[NSC:P41A] PROCESS' in x and 'status=5' in x for x in lines))
print('PROCESS_readerr1',sum('[NSC:P41A] PROCESS' in x and 'readerr=1' in x for x in lines))
evtops=Counter(); self_names=Counter(); self_resolved=Counter(); self_exec=Counter(); native_names=Counter(); modes=Counter()
for x in lines:
    if '[NSC:P41A] EVT236' in x:
        m=re.search(r'op=(-?\d+)',x)
        if m: evtops[int(m.group(1))]+=1
    if '[NSC:P41A] EVT121_SELF' in x:
        n=re.search(r'text=([^ ]*)',x); r=re.search(r'resolved=(-?\d+)',x); e=re.search(r'executed=(\d+)',x)
        if n: self_names[n.group(1)]+=1
        if r: self_resolved[int(r.group(1))]+=1
        if e: self_exec[int(e.group(1))]+=1
    if '[NSC:P41A] EVT121_NATIVE' in x:
        n=re.search(r'text=([^ ]*)',x)
        if n: native_names[n.group(1)]+=1
    if '[NSC:P41A] OUGI_CORE' in x:
        m=re.search(r'mode=(\d+)',x)
        if m: modes[int(m.group(1))]+=1
print('EVT236 opcodes:',dict(sorted(evtops.items())))
print('EVT121 SELF names:',dict(self_names))
print('EVT121 SELF resolved:',dict(sorted(self_resolved.items())))
print('EVT121 SELF executed:',dict(sorted(self_exec.items())))
print('COND_HIGHBANK_RESOLVED',sum(k in range(512,517) for k in self_resolved.elements()))
print('EVT121 native names:',dict(native_names))
print('OUGI modes:',dict(sorted(modes.items())))
print('\n--- focused state trace ---')
for x in lines:
    if any(k in x for k in ('EVT13_RAW','EVT13_AWAKE','EVT121_SELF','EVT121_NATIVE','OUGI_RAW','OUGI_CORE')):
        print(x)
