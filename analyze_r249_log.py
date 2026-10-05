#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=2:
    print('usage: analyze_r249_log.py <uzuy_log.txt>'); sys.exit(2)
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
for tag in ['READY','MODEL_INIT','RESOURCE_GATE','CHUNK_GATE','ALLOC']:
    hits=[x for x in lines if '[NSC:R249]' in x and tag in x]
    print(f'{tag}_COUNT={len(hits)}')
    for x in hits[:16]: print(x)
res=[x for x in lines if '[NSC:R249] RESOURCE_GATE target=1' in x]
chk=[x for x in lines if '[NSC:R249] CHUNK_GATE target=1' in x]
alc=[x for x in lines if '[NSC:R249] ALLOC target=1' in x]
post=[x for x in lines if '[NSC:R249] MODEL_INIT phase=post target=1' in x]
def ptr_result(line):
    m=re.search(r'result=(0x[0-9a-fA-F]+|\(nil\)|0x0)',line); return m.group(1) if m else None
def nonnull(v): return v not in (None,'0x0','(nil)')
if not res:
    print('DECISION=NO_TARGET_RESOURCE_GATE'); sys.exit(0)
r=ptr_result(res[-1]); print('RESOURCE_RESULT='+str(r))
if not nonnull(r): print('DECISION=FILE_RESOURCE_MISSING'); sys.exit(0)
if not chk:
    print('DECISION=RESOURCE_PASS_BUT_NO_CHUNK_GATE'); sys.exit(0)
c=ptr_result(chk[-1]); print('CHUNK_RESULT='+str(c))
if not nonnull(c): print('DECISION=CHUNK_KEY_OR_TYPE_MISS'); sys.exit(0)
alloc3=[]
for x in alc:
    m=re.search(r'size=(\d+)',x)
    if m and int(m.group(1))==944: alloc3.append(x)
if not alloc3:
    print('DECISION=CHUNK_PASS_BUT_NO_MODEL_ALLOC_3B0'); sys.exit(0)
a=ptr_result(alloc3[-1]); print('ALLOC_3B0_RESULT='+str(a))
if not nonnull(a): print('DECISION=MODEL_OBJECT_ALLOC_FAIL'); sys.exit(0)
if post and 'ready90=0x0' not in post[-1] and 'ready90=(nil)' not in post[-1]:
    print('DECISION=CREATE_READY_PRODUCER_PASS')
else:
    print('DECISION=POST_ALLOC_CONSTRUCTOR_OR_STORE_CORRIDOR')
