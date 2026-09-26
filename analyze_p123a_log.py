#!/usr/bin/env python3
import sys,re
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
s=open(p,errors='ignore').read().splitlines()
keys=['[NSC:P123A] READY','[NSC:P123A] GATE','[NSC:P123A] ACTOR_C48','[NSC:P123A] PEER_C48','[NSC:P123A] TYPE9','[NSC:P123A] LOOKUP','code=710','index=710']
for k in keys:
    hits=[x for x in s if k in x]
    print(f'## {k} ({len(hits)})')
    for x in hits[:40]: print(x)
