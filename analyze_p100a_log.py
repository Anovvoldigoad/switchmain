#!/usr/bin/env python3
import re,sys,collections
text=open(sys.argv[1],errors='ignore').read().splitlines()
rows=[]
for l in text:
 if '[NSC:P100A] LANDMARK' not in l: continue
 d={k:v for k,v in re.findall(r'(\w+)=([^ ]+)',l)}
 rows.append(d)
print('P100A_READY',sum('[NSC:P100A] READY' in l for l in text),'LANDMARKS',len(rows))
by=collections.defaultdict(list)
for d in rows: by[int(d.get('char','-1'))].append(d)
for cid,rs in sorted(by.items()):
 print('CHAR',cid)
 for d in rs:
  print(' ',d.get('stage'),'action',d.get('action'),'e94',d.get('e94'),'aux0',d.get('aux0'),'aux1',d.get('aux1'))
print('DECISION: successful vanilla should reach ENTRY and REQUEST710. Compare the last common landmark with custom; first missing custom stage brackets the upstream branch that prevents 710.')
