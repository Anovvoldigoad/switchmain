#!/usr/bin/env python3
import re,sys,collections
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
lines=open(p,errors='replace').read().splitlines()
ready=[x for x in lines if '[NSC:P100C] READY' in x]
oracle=[x for x in lines if '[NSC:P100C] ORACLE' in x]
print('P100C_READY',len(ready))
if ready: print(ready[-1])
print('P100C_ORACLE',len(oracle))
rx=re.compile(r'tag=(\S+).*?char=(\d+).*?caller_off=0x([0-9a-fA-F]+).*?ret=(\d+).*?route13=(\d+)')
groups=collections.defaultdict(list)
for ln in oracle:
 m=rx.search(ln)
 if not m: continue
 tag,cid,caller,ret,r13=m.groups()
 groups[int(cid)].append((tag,int(caller,16),int(ret),int(r13),ln))
for cid,rows in sorted(groups.items()):
 print(f'\nCHAR {cid}')
 for tag,caller,ret,r13,ln in rows:
  print(f'  {tag:16s} caller=0x{caller:x} ret={ret} (0x{ret:x}) route13={r13}')
 r=[x for x in rows if x[0]=='ROUTE13']
 if r:
  print('  ROUTE13_RESULT', 'PASS_TO_710_PATH' if any(x[3] for x in r) else 'DIVERGES_BEFORE_710_LOOKUP')
 else:
  print('  ROUTE13_RESULT NOT_REACHED')
print('\nInterpretation: compare vanilla successful actor vs custom actor. ROUTE13 ret=19/0x13 is the native branch that continues toward lookup/remap and proven PlayAction(710).')
