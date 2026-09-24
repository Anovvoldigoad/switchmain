#!/usr/bin/env python3
import re, sys
from pathlib import Path
if len(sys.argv) != 2:
    raise SystemExit('usage: analyze_p96a_log.py uzuy_log.txt')
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
ready=[x for x in lines if '[NSC:P96A] READY' in x]
rows=[x for x in lines if '[NSC:P96A] ACTDESC' in x]
print('P96A_READY', len(ready))
print('ACTDESC_ROWS', len(rows))
pat=re.compile(r"char=(\d+).*semantic=(\d+).*caller_off=0x([0-9a-f]+).*code=(-?\d+).*action=(\d+).*cur_action=(\d+).*e70=(\d+).*e90=(\d+).*mapped_generic=(\d+).*i707_desc=0x([0-9a-f]+).*d94=(\d+) key707='([^']*)'")
parsed=[]
for x in rows:
    m=pat.search(x)
    if m:
        parsed.append(dict(char=int(m[1]), semantic=int(m[2]), caller=int(m[3],16), code=int(m[4]), action=int(m[5]), cur=int(m[6]), e70=int(m[7]), e90=int(m[8]), mapped=int(m[9]), desc=int(m[10],16), d94=int(m[11]), key=m[12], line=x))
for label, filt in [
    ('VANILLA_710', lambda r:r['semantic']==0 and r['code']==710),
    ('CUSTOM_708', lambda r:r['semantic']==1 and r['code']==708),
    ('CUSTOM_707_ENTRY', lambda r:r['semantic']==1 and r['code']==707),
]:
    hit=next((r for r in parsed if filt(r)), None)
    print('\n'+label)
    if not hit: print('  NOT_FOUND'); continue
    for k in ['char','caller','code','action','cur','e70','e90','mapped','desc','d94','key']:
        v=hit[k]
        print(f'  {k}={hex(v) if k in ("caller","desc") else v}')
    print('  raw=',hit['line'])
if parsed:
    print('\nUNIQUE_KEY707')
    seen=set()
    for r in parsed:
        key=(r['semantic'],r['char'],r['mapped'],r['desc'],r['key'])
        if key in seen: continue
        seen.add(key)
        print(f"  semantic={r['semantic']} char={r['char']} mapped={r['mapped']} desc=0x{r['desc']:x} key707={r['key']!r}")
