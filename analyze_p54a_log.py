#!/usr/bin/env python3
from pathlib import Path
import re,sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
s=p.read_text(errors='replace')
keys=['[NSC:P50A] READY','[NSC:P54A] READY','[NSC:P54A] DIRECT98_OWNER','[NSC:P54A] DIRECT100_OWNER','[NSC:P54A] ACTION_ROUTE']
for k in keys:
    rows=[x for x in s.splitlines() if k in x]
    print(f'\n{k}: {len(rows)}')
    for x in rows[-80:]: print(x)
print('\ncustom direct-owner hits:')
for x in s.splitlines():
    if '[NSC:P54A] DIRECT' in x:
        m=re.search(r'char=(\d+)',x)
        if m and int(m.group(1))>280: print(x)
