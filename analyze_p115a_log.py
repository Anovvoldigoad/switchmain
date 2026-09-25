#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
lines=p.read_text(errors='replace').splitlines()
ts_re=re.compile(r'^\[\s*([0-9.]+)\]')
ready=[(i,l) for i,l in enumerate(lines,1) if '[NSC:P115A] READY' in l]
evt_re=re.compile(r'\[NSC:P115A\] EVT_GATE .*?char=(\d+) action=(\d+) e94=(\d+).*?pchar=(\d+).*?raw_type=(\d+) norm_type=(\d+) pass=(\d+)')
act_re=re.compile(r'\[NSC:P115A\] ACTOR_C48 .*?char=(\d+) action=(\d+) e94=(\d+).*?pchar=(\d+).*?raw_type=(\d+) target_off=0x([0-9a-fA-F]+) ret=(\d+)')
peer_re=re.compile(r'\[NSC:P115A\] PEER_C48 .*?char=(\d+) action=(\d+) e94=(\d+).*?pchar=(\d+).*?raw_type=(\d+) target_off=0x([0-9a-fA-F]+) ret=(\d+)')
play_re=re.compile(r'\[NSC:P59A\] PLAY_CALL .*?side=(\d+) char=(\d+) index=(\d+) .*?caller_off=0x([0-9a-fA-F]+)')
events=[]; actors=[]; peers=[]; plays=[]
for i,l in enumerate(lines,1):
    m=ts_re.match(l); t=float(m.group(1)) if m else None
    q=evt_re.search(l)
    if q: events.append((i,t,*map(int,q.groups()),l))
    q=act_re.search(l)
    if q:
        g=q.groups(); actors.append((i,t,int(g[0]),int(g[1]),int(g[2]),int(g[3]),int(g[4]),int(g[5],16),int(g[6]),l))
    q=peer_re.search(l)
    if q:
        g=q.groups(); peers.append((i,t,int(g[0]),int(g[1]),int(g[2]),int(g[3]),int(g[4]),int(g[5],16),int(g[6]),l))
    q=play_re.search(l)
    if q and t is not None: plays.append((i,t,int(q.group(1)),int(q.group(2)),int(q.group(3)),int(q.group(4),16),l))
print('READY_COUNT',len(ready))
for i,l in ready: print('READY',i,l)
print('EVT_GATE_COUNT',len(events),'ACTOR_C48_COUNT',len(actors),'PEER_C48_COUNT',len(peers))
for x in events: print('EVT',x[0],'t',x[1],'char',x[2],'action',x[3],'e94',x[4],'pchar',x[5],'raw',x[6],'norm',x[7],'pass',x[8])
for x in actors: print('ACTOR_C48',x[0],'t',x[1],'char',x[2],'action',x[3],'e94',x[4],'pchar',x[5],'raw',x[6],'target',hex(x[7]),'ret',x[8])
for x in peers: print('PEER_C48',x[0],'t',x[1],'char',x[2],'action',x[3],'e94',x[4],'pchar',x[5],'raw',x[6],'target',hex(x[7]),'ret',x[8])
starts=[x for x in plays if x[2]==0 and x[4]==700]
windows=[]
for s in starts:
    end=None
    for x in plays:
        if x[1] < s[1]: continue
        if x[1] > s[1]+6.0: break
        if x[2]==0 and x[3]==s[3] and x[4] in (710,261): end=x; break
    et=end[1] if end else s[1]+6.0
    E=[x for x in events if x[1] is not None and s[1]-0.05<=x[1]<=et+0.05 and x[2]==s[3]]
    A=[x for x in actors if x[1] is not None and s[1]-0.05<=x[1]<=et+0.05 and x[2]==s[3]]
    P=[x for x in peers if x[1] is not None and s[1]-0.05<=x[1]<=et+0.05 and x[2]==s[3]]
    windows.append((s,end,E,A,P))
print('UJ_WINDOWS',len(windows))
for s,e,E,A,P in windows:
    print('UJ char',s[3],'start',s[1],'terminal',e[4] if e else None,'end',e[1] if e else None,
          'evt',[(x[6],x[8]) for x in E],'actor_c48',[(x[7],x[8]) for x in A],'peer_c48',[(x[7],x[8]) for x in P])
custom=[w for w in windows if w[0][3]==281]
if not custom:
    print('DECISION=NO_CUSTOM_UJ_WINDOW_FOUND')
else:
    s,e,E,A,P=custom[-1]
    if not E:
        print('DECISION=CUSTOM_NEVER_REACHES_77C474_EVENT_GATE')
    elif any(x[8]==0 for x in E):
        print('DECISION=CUSTOM_EVENT_TYPE10_11_GATE_FAIL')
    elif not A:
        print('DECISION=CUSTOM_EVENT_GATE_PASSES_BUT_ACTOR_C48_NOT_REACHED_UNEXPECTED')
    elif any(x[8]==0 for x in A):
        print('DECISION=CUSTOM_ACTOR_C48_GATE_FAIL')
    elif not P:
        print('DECISION=CUSTOM_ACTOR_C48_PASSES_BUT_PEER_C48_NOT_REACHED_UNEXPECTED')
    elif any(x[8]==0 for x in P):
        print('DECISION=CUSTOM_PEER_C48_GATE_FAIL')
    else:
        print('DECISION=CUSTOM_PASSES_ALL_THREE_GATES_DIVERGENCE_AFTER_77C4A8')
