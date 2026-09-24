#!/usr/bin/env python3
import re,sys
p=sys.argv[1]
lines=open(p,errors='replace').read().splitlines()
for s in ('[NSC:P97A] READY','[NSC:P97A] GUARD','index=708','index=710','caller_off=0x7725d0','caller_off=0x7e6ec8'):
 xs=[(i+1,l) for i,l in enumerate(lines) if s in l]
 print(f'\n## {s} count={len(xs)}')
 for i,l in xs[:80]: print(f'{i}: {l}')
