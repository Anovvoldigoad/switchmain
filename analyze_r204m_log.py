#!/usr/bin/env python3
import re, sys
from collections import Counter, defaultdict
from pathlib import Path
p=Path(sys.argv[1]); lines=p.read_text(errors="replace").splitlines()
print(f"FILE={p}")
print(f"LINES={len(lines)}")
print(f"CPU_AI_PATCH_LINES={sum('Applying IPS patch from mod \"CPU_AI_MAX_PLUS_' in x for x in lines)}")
print(f"NCE_UNMAPPED={sum('Unmapped InvalidateNCE' in x for x in lines)}")
markers=[
 'PROCESS_ENTER','FILE_OPEN','READ_DISPATCH_ENTER','READ_DISPATCH_EXIT',
 'READ_STAGE_ENTER','READ_STAGE_EXIT','REQUEST_FINALIZE_ENTER','REQUEST_FINALIZE_EXIT',
 'READ_CLEANUP_ENTER','READ_CLEANUP_EXIT','PROCESS_EXIT','STATE_SET','SUCCESS_SET',
 'RESOURCE_LOOKUP','CHUNK_LOW','OWNER_REGISTER','OWNER_READY','REGISTRY_PROCESS'
]
for tag in markers:
    xs=[x for x in lines if f'[NSC:R204M] {tag}' in x]
    print(f'{tag}={len(xs)}')
    for x in xs[:12]: print(x)
paths=['bod1.xfbin','bod1_col2.xfbin','bod1_col3.xfbin','bod1acc.bin.xfbin','mtobcharsel.xfbin','mtobprm_load.bin.xfbin']
print('--- PATH MATRIX ---')
for path in paths:
    print(path)
    for tag in markers:
        n=sum(f'[NSC:R204M] {tag}' in x and path in x for x in lines)
        if n: print(f'  {tag}={n}')
methods=Counter()
for x in lines:
    if '[NSC:R204M] READ_DISPATCH_ENTER' in x:
        m=re.search(r'method_off=(0x[0-9a-fA-F]+).*path=(.*)$',x)
        if m: methods[(m.group(1),m.group(2))]+=1
print('--- PROVIDER METHODS ---')
for (off,path),n in methods.most_common(30): print(n,off,path)
