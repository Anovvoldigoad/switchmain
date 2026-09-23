#!/usr/bin/env python3
import re,sys,collections
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'; lines=open(p,errors='replace').read().splitlines()
r=[x for x in lines if '[NSC:P88A]' in x]; print('P88_LINES',len(r));
for tag in ['READY','PROD','HELPER_8B30E4','CTRL_7C553C','INPUT_7C6074','MASK_7C5FB0','STATE2_7D5C10','GATE_78FDC0','ACTOR_7E24EC']:
 q=[x for x in r if '] '+tag in x]; print(tag,len(q))
# summarize helper by char/bda4/bdc8/ret without assuming fixture IDs
pat=re.compile(r'char=(\d+).*ret=(\d+).*bda4=(-?\d+)->(-?\d+).*bdc8=(-?\d+)->(-?\d+)')
c=collections.Counter()
for x in r:
 if 'HELPER_8B30E4' not in x: continue
 m=pat.search(x)
 if m:c[(m.group(1),m.group(3),m.group(5),m.group(2))]+=1
print('\nHELPER char,bda4,bdc8,ret,count')
for k,n in sorted(c.items()):print(*k,n)
print('\nPHASE3 HELPER / nearby decisive predicates')
for i,x in enumerate(lines):
 if '[NSC:P88A]' in x and ('HELPER_8B30E4' in x or 'STATE2_7D5C10' in x or 'GATE_78FDC0' in x or 'ACTOR_7E24EC' in x) and ('bda4=3->' in x or 'bda4=4->' in x): print(f'{i+1}: {x}')
