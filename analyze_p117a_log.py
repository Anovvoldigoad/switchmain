#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
lines=p.read_text(errors='replace').splitlines()
ts_re=re.compile(r'^\[\s*([0-9]+\.[0-9]+)\]')
event_re=re.compile(r'\[NSC:P117A\] EVENT n=(\d+) event=(0x[0-9a-fA-F]+|\(nil\)) caller_off=0x([0-9a-fA-F]+) raw_type=(\d+) norm_type=(\d+) type10_11=(\d+) gate_ret=(\d+) payload28=([0-9a-fA-F]+) mask48=0x([0-9a-fA-F]+)')
play_re=re.compile(r'\[NSC:P59A\] PLAY_CALL .*?char=(\d+) index=(\d+) .*?pre=(\d+) post=(\d+)')
ready=sum('[NSC:P117A] READY' in x and 'probe_ok=1' in x for x in lines)
events=[]; plays=[]
for i,s in enumerate(lines,1):
    tm=ts_re.search(s); t=float(tm.group(1)) if tm else None
    m=event_re.search(s)
    if m:
        events.append(dict(line=i,t=t,n=int(m.group(1)),event=m.group(2),caller=int(m.group(3),16),raw=int(m.group(4)),norm=int(m.group(5)),t1011=int(m.group(6)),ret=int(m.group(7)),p28=m.group(8),mask=m.group(9)))
    m=play_re.search(s)
    if m:
        plays.append(dict(line=i,t=t,char=int(m.group(1)),index=int(m.group(2)),pre=int(m.group(3)),post=int(m.group(4))))
print('P117_READY',ready)
print('EVENT_ROWS',len(events))
from collections import Counter
print('RAW_TYPE_COUNTS',dict(sorted(Counter(e['raw'] for e in events).items())))
print('TYPE10_11_ROWS',sum(e['t1011'] for e in events))
for e in events:
    if e['t1011']:
        print(' TYPE10_11 line',e['line'],'t',e['t'],'raw',e['raw'],'ret',e['ret'],'event',e['event'])
custom=[x for x in plays if x['char']==281 and x['index'] in (700,707,708,261,74)]
if custom:
    print('CUSTOM281_ACTIONS')
    for x in custom: print(' ',x)
    t0=min(x['t'] for x in custom if x['t'] is not None)-1.0
    t1=max(x['t'] for x in custom if x['t'] is not None)+1.0
    ce=[e for e in events if e['t'] is not None and t0<=e['t']<=t1]
    print('CUSTOM281_WINDOW',t0,t1,'EVENTS',len(ce),'TYPE10_11',sum(e['t1011'] for e in ce),'RAW',dict(sorted(Counter(e['raw'] for e in ce).items())))
    for e in ce: print('  EVENT',e)
# successful vanilla marker = non-281 PlayAction710
van710=[x for x in plays if x['char']!=281 and x['index']==710]
if van710:
    v=van710[0]; t0=v['t']-3.0; t1=v['t']+0.5
    ve=[e for e in events if e['t'] is not None and t0<=e['t']<=t1]
    print('VANILLA710',v)
    print('VANILLA_WINDOW',t0,t1,'EVENTS',len(ve),'TYPE10_11',sum(e['t1011'] for e in ve),'RAW',dict(sorted(Counter(e['raw'] for e in ve).items())))
    for e in ve: print('  EVENT',e)
if custom and van710:
    c_t0=min(x['t'] for x in custom if x['t'] is not None)-1.0
    c_t1=max(x['t'] for x in custom if x['t'] is not None)+1.0
    c1011=[e for e in events if e['t'] is not None and c_t0<=e['t']<=c_t1 and e['t1011']]
    v_t0=van710[0]['t']-3.0; v_t1=van710[0]['t']+0.5
    v1011=[e for e in events if e['t'] is not None and v_t0<=e['t']<=v_t1 and e['t1011']]
    if v1011 and not c1011:
        print('DECISION=VANILLA_HAS_TYPE10_11_CUSTOM_MISSING_EVENT_STREAM')
        print('NEXT=back-slice event descriptor/producer feeding main+0x77B560; do not force session/state')
    elif v1011 and c1011:
        print('DECISION=BOTH_HAVE_TYPE10_11')
        print('NEXT=probe actor/peer C48 readiness gate one-at-a-time')
    else:
        print('DECISION=NO_CLEAN_TYPE10_11_COMPARISON')
