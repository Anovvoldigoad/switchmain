#!/usr/bin/env python3
import re,sys
from collections import defaultdict
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
lines=open(p,errors='replace').read().splitlines()
ready=[x for x in lines if '[NSC:P56B] READY' in x]
pat=re.compile(r'CONTROL_CAND tag=(\S+) seq=(\d+) rank=(\d+) base=0x([0-9a-fA-F]+) bool=(\d+) ones=(\d+).*?uj=(-?\d+) jutsu=(-?\d+).*?awake=(-?\d+)')
by=defaultdict(list)
for line in lines:
    m=pat.search(line)
    if m:
        tag,seq,rank,base,bo,ones,uj,jutsu,awake=m.groups()
        by[tag].append((int(base,16),int(rank),int(bo),int(ones),int(uj),int(jutsu),int(awake),int(seq)))
print('READY',len(ready))
for tag,rows in by.items():
    print(tag,'rows',len(rows))
    for r in rows[:16]: print(' ',r)
sets={tag:{x[0] for x in rows} for tag,rows in by.items()}
if 'VANILLA_PLAY700' in sets and 'CUSTOM_O14_UJ_ENABLE' in sets:
    common=sorted(sets['VANILLA_PLAY700'] & sets['CUSTOM_O14_UJ_ENABLE'])
    print('COMMON_BASES',','.join(hex(x) for x in common) if common else '<none>')
else:
    print('COMMON_BASES <insufficient snapshots>')
