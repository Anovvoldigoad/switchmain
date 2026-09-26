#!/usr/bin/env python3
import sys,re
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
lines=open(p,errors='ignore').read().splitlines()
keys=['[NSC:P128A] READY','[NSC:P124A] GATE','[NSC:P128A] POST_OUTER','[NSC:P125A] CLEANUP','caller_off=0x7e6ec8 code=710']
for k in keys:
    rows=[(i+1,l) for i,l in enumerate(lines) if k in l]
    print(f'\n{k}: {len(rows)}')
    for i,l in rows[:20]: print(i,l)
print('\ncustom native710:')
rows=[(i+1,l) for i,l in enumerate(lines) if 'char=281' in l and ('code=710' in l or 'caller_off=0x7e6ec8' in l)]
print(len(rows))
for i,l in rows[:20]: print(i,l)
