#!/usr/bin/env python3
from pathlib import Path
import re,sys,collections
if len(sys.argv)!=2:
    raise SystemExit('usage: python3 analyze_p111a_log.py <uzuy_log.txt>')
p=Path(sys.argv[1]); lines=p.read_text(errors='replace').splitlines()
ready=[(i+1,l) for i,l in enumerate(lines) if '[NSC:P111A] READY' in l]
print('P111_READY_COUNT',len(ready))
for i,l in ready[:3]: print(' READY',i,l.split('[NSC:P111A]',1)[-1].strip())
pat=re.compile(r'\[NSC:P111A\] VSTATE n=(\d+) actor=(0x[0-9a-fA-F]+) side=(\d+) char=(\d+) req=(\d+) arg2=(\d+) arg3=(\d+) caller_off=(0x[0-9a-fA-F]+) ret=(\d+) action=(\d+)->(\d+) e94=(\d+)->(\d+) e98=(\d+)->(\d+) e9c=(\d+)->(\d+)')
rows=[]
for i,l in enumerate(lines,1):
    m=pat.search(l)
    if m:
        vals=m.groups(); rows.append({
            'line':i,'n':int(vals[0]),'actor':vals[1],'side':int(vals[2]),'char':int(vals[3]),
            'req':int(vals[4]),'arg2':int(vals[5]),'arg3':int(vals[6]),'caller':vals[7],'ret':int(vals[8]),
            'a0':int(vals[9]),'a1':int(vals[10]),'e940':int(vals[11]),'e941':int(vals[12]),
            'e980':int(vals[13]),'e981':int(vals[14]),'e9c0':int(vals[15]),'e9c1':int(vals[16])})
print('P111_VSTATE_COUNT',len(rows))
by_req=collections.Counter((r['req'],r['caller']) for r in rows)
print('REQUEST_CALLERS')
for (req,caller),count in sorted(by_req.items()): print(f' req={req:3d} caller={caller} count={count}')
by_actor=collections.defaultdict(list)
for r in rows: by_actor[(r['actor'],r['side'],r['char'])].append(r)
print('ACTOR_CHAINS')
for key,rs in sorted(by_actor.items(), key=lambda kv:min(x['line'] for x in kv[1])):
    print(f' actor={key[0]} side={key[1]} char={key[2]} rows={len(rs)}')
    for r in rs:
        print(f"   L{r['line']} req={r['req']} caller={r['caller']} action={r['a0']}->{r['a1']} e94={r['e940']}->{r['e941']} e98={r['e980']}->{r['e981']} e9c={r['e9c0']}->{r['e9c1']} ret={r['ret']}")
play12=[]
p12=re.compile(r'\[NSC:P59A\] PLAY_CALL .*?actor=(0x[0-9a-fA-F]+).*?side=(\d+).*?char=(\d+).*?index=12\b.*?pre=(\d+) post=(\d+).*?caller_off=(0x[0-9a-fA-F]+)')
for i,l in enumerate(lines,1):
    m=p12.search(l)
    if m: play12.append((i,)+m.groups())
print('PLAYACTION12_COUNT',len(play12))
for x in play12: print(f' L{x[0]} actor={x[1]} side={x[2]} char={x[3]} pre={x[4]} post={x[5]} caller={x[6]}')
# Detect actors observed at committed state126 in inherited traces, and whether a req126 row exists.
state126=collections.defaultdict(list)
core126=re.compile(r'\[NSC:P93A\] CORE .*?actor=(0x[0-9a-fA-F]+).*?side=(\d+).*?char=(\d+).*?e94=0000007e\b')
for i,l in enumerate(lines,1):
    m=core126.search(l)
    if m: state126[m.groups()].append(i)
req126actors={(r['actor'],str(r['side']),str(r['char'])) for r in rows if r['req']==126}
print('STATE126_GATEWAY_AUDIT')
for key,lins in sorted(state126.items(), key=lambda kv:kv[1][0]):
    has=key in req126actors
    print(f' actor={key[0]} side={key[1]} char={key[2]} first_e94_126=L{lins[0]} req126_via_7A89A4={int(has)}')
    if not has: print('   POSSIBLE_DIRECT_OR_ALTERNATE_SETTER_126=1')
# Short decision summary.
print('DECISION_HINTS')
print(' - Compare victim-side req125/126 + PlayAction12 against failing victim req39/121.')
print(' - If E94=126 appears but req126_via_7A89A4=0, next provenance target is the alternate/simple setter family, not another state remap.')
