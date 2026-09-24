#!/usr/bin/env python3
import argparse,re,sys
from collections import Counter,defaultdict
ap=argparse.ArgumentParser()
ap.add_argument('log')
ap.add_argument('--control-char',type=int,default=91)
ap.add_argument('--custom-char',type=int,default=281)
a=ap.parse_args()
lines=open(a.log,errors='replace').read().splitlines()
ready=[x for x in lines if '[NSC:P104B] READY' in x]
gates=[x for x in lines if '[NSC:P104B] GATE' in x]
print('READY',len(ready)); [print(x) for x in ready[-3:]]
print('GATE total',len(gates))
rx=re.compile(
 r'side=(\d+).*?char=(\d+).*?caller_off=0x([0-9a-fA-F]+).*?action=(\d+)->(\d+).*?pred=(\d+).*?'
 r'gate12240_pre=([0-9a-fA-F]+).*?gate12240_post=([0-9a-fA-F]+).*?gate12240_changed=(\d+).*?'
 r'slot4c0_off=0x([0-9a-fA-F]+).*?slot520_off=0x([0-9a-fA-F]+)')
rows=[]
for x in gates:
 m=rx.search(x)
 if not m:
  print('UNPARSED:',x)
  continue
 side,cid,caller,pre,post,pred,gpre,gpost,changed,s4,s5=m.groups()
 rows.append((int(side),int(cid),int(caller,16),int(pre),int(post),int(pred),int(gpre,16),int(gpost,16),int(changed),int(s4,16),int(s5,16),x))

bad_side=[r for r in rows if r[0]!=0]
bad_caller=[r for r in rows if r[2]!=0x7DE028]
bad_slot=[r for r in rows if r[9]!=0x7DDD94 or r[10]!=0x7E64D4]
if bad_side: print('ERROR non-player-side rows:',len(bad_side))
if bad_caller: print('ERROR unexpected caller rows:',len(bad_caller))
if bad_slot: print('ERROR unexpected sibling vtable rows:',len(bad_slot))
if bad_side or bad_caller or bad_slot:
 print('LOG_VALIDATION=FAIL')
 sys.exit(2)
print('LOG_VALIDATION=PASS')

by=defaultdict(list)
for r in rows: by[r[1]].append(r)
for cid in sorted(by):
 rs=by[cid]
 print(f'char {cid}: hits={len(rs)} gate_pairs={Counter((r[3],r[5],r[6],r[7],r[8]) for r in rs)}')

for label,cid in [('CONTROL',a.control_char),('CUSTOM',a.custom_char)]:
 rs=by.get(cid,[])
 print(f'\n{label} char={cid} hits={len(rs)}')
 for r in rs[:60]: print(r[-1])
 if not rs: print('NO_FOCUSED_GATE_HIT')
 changed=[r for r in rs if r[8]!=0]
 print('gate12240_changed_hits',len(changed))
 print('pred_counts',Counter(r[5] for r in rs))
 print('gate_post_zero/nonzero',Counter(0 if r[7]==0 else 1 for r in rs))

print('\nInterpretation:')
print('- gate12240_post is the P104B authoritative gate2 sample: captured after Orig(0x7EE8E0), immediately before hook return.')
print('- pred=0 => native +0x4C0 will take the first early-return branch at 0x7DE028.')
print('- pred!=0 and gate12240_post=0 => second gate is closed at the post-predicate sample.')
print('- pred!=0 and gate12240_post!=0 => both sampled gates are open; path may continue toward the 262/261 selector.')
print('- gate12240_changed=1 => predicate execution changed gate2; do not use the pre value for diagnosis.')
print('- Compare successful vanilla control and failing custom from the SAME session; use the first reproducible gate difference as the next target.')
