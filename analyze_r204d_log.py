#!/usr/bin/env python3
import sys
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit('usage: analyze_r204d_log.py <uzuy_log.txt>')
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
events=[x for x in lines if '[NSC:R204D]' in x]
print(f'R204D_LINES={len(events)}')
for key in ('READY','LOAD_CREATE','LOAD_REQ','FILE_OPEN','PROCESS','STATE_SET','SUCCESS_SET','LOAD_STATUS','CHUNK'):
    xs=[x for x in events if f'] {key}' in x]
    print(f'{key}={len(xs)}')
for needle in ('mtobprm_load.bin.xfbin','mtobcharsel.xfbin','mtobbod1'):
    print(f'--- {needle} ---')
    for x in events:
        if needle in x: print(x)
