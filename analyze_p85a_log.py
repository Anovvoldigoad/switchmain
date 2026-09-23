#!/usr/bin/env python3
import re, sys, collections
from pathlib import Path
if len(sys.argv)<2: raise SystemExit('usage: python analyze_p85a_log.py uzuy_log.txt')
p=Path(sys.argv[1]); lines=p.read_text(errors='replace').splitlines()
f58={}; inp={}; mp={}
rxseq=re.compile(r'\bseq=(\d+)')
def kv(line): return dict(re.findall(r'([A-Za-z0-9_]+)=([0-9A-Fa-fx\-]+)',line))
for line in lines:
    if '[NSC:P85A] F58 ' in line:
        d=kv(line); f58[int(d['seq'])]=d
    elif '[NSC:P85A] INPUT ' in line:
        d=kv(line); inp[int(d['seq'])]=d
    elif '[NSC:P85A] MAP ' in line:
        d=kv(line); mp[int(d['seq'])]=d
print(f'P85 F58 records={len(f58)} input={len(inp)} map={len(mp)}')
# Signature counts by char and native return. Raw current/edge inputs are kept exactly.
c=collections.Counter()
for s,d in f58.items():
    i=inp.get(s,{})
    sig=(d.get('char'),d.get('ret'),d.get('semantic'),d.get('e94'),d.get('e9c'),
         i.get('i3fc'),i.get('i404'),i.get('i408'),i.get('i40c'),i.get('i410'),
         i.get('m594'),i.get('m598'),i.get('m59c'),i.get('m5a0'))
    c[sig]+=1
print('\nTop signatures:')
for sig,n in c.most_common(100): print(n, sig)
print('\nF58 ret census:')
rr=collections.Counter((d.get('char'),d.get('semantic'),d.get('ret')) for d in f58.values())
for k,n in sorted(rr.items()): print(k,n)
# Candidate raw bits that occur in ret=1 vs ret=0, by char.
for char in sorted({d.get('char') for d in f58.values()}):
    rows=[]
    for s,d in f58.items():
        if d.get('char')!=char or s not in inp: continue
        i=inp[s]; rows.append((int(d.get('ret','0'),0),{k:int(v,16) for k,v in i.items() if k.startswith('i') or k.startswith('m')}))
    if not rows: continue
    print(f'\nchar={char} records={len(rows)}')
    keys=sorted(rows[0][1])
    for k in keys:
        vals0=sorted({r[1][k] for r in rows if r[0]==0}); vals1=sorted({r[1][k] for r in rows if r[0]!=0})
        if vals0!=vals1:
            print(f'  {k}: ret0={[hex(x) for x in vals0[:16]]} ret1={[hex(x) for x in vals1[:16]]}')
