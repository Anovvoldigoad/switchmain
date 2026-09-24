#!/usr/bin/env python3
import argparse,re
from collections import Counter,defaultdict
ap=argparse.ArgumentParser()
ap.add_argument('log')
ap.add_argument('--control-char',type=int,default=91)
ap.add_argument('--custom-char',type=int,default=281)
a=ap.parse_args()
lines=open(a.log,errors='replace').read().splitlines()
ready=[x for x in lines if '[NSC:P104A] READY' in x]
gates=[x for x in lines if '[NSC:P104A] GATE' in x]
print('READY',len(ready)); [print(x) for x in ready[-3:]]
print('GATE total',len(gates))
rx=re.compile(r'char=(\d+).*?action=(\d+)->(\d+).*?pred=(\d+).*?gate12240=([0-9a-fA-F]+).*?slot4c0_off=0x([0-9a-fA-F]+).*?slot520_off=0x([0-9a-fA-F]+)')
rows=[]
for x in gates:
 m=rx.search(x)
 if not m:continue
 cid,pre,post,pred,flag,s4,s5=m.groups(); rows.append((int(cid),int(pre),int(post),int(pred),int(flag,16),int(s4,16),int(s5,16),x))
by=defaultdict(list)
for r in rows:by[r[0]].append(r)
for cid in sorted(by):
 print(f'char {cid}: hits={len(by[cid])} pairs={Counter((r[1],r[3],r[4]) for r in by[cid])}')
for label,cid in [('CONTROL',a.control_char),('CUSTOM',a.custom_char)]:
 rs=by.get(cid,[])
 print(f'\n{label} char={cid} hits={len(rs)}')
 for r in rs[:40]:print(r[-1])
 if not rs:print('NO_FOCUSED_GATE_HIT')
print('\nInterpretation:')
print('- pred=0 => +0x4C0 returns early at 0x7DE028 before 261 selector.')
print('- pred!=0 but gate12240=0 => +0x4C0 returns early at 0x7DE030.')
print('- pred!=0 and gate12240!=0 => both gates open; path may continue toward 262/261.')
print('- Compare successful vanilla control and failing custom in the SAME run.')
