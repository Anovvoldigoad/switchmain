#!/usr/bin/env python3
from pathlib import Path
import sys,re,hashlib
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
text=p.read_text(errors='replace')
lines=text.splitlines()
print('file='+str(p))
print('bytes='+str(p.stat().st_size))
print('sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
markers=['READY','TARGET_REGISTRY_CAPTURE','CREATE_ENTER','DESCRIPTOR_LOOKUP','MODEL tag=init_pre','MODEL tag=init_post','IDENTITY_LOOKUP','READY_PREDICATE']
for m in markers:
    hits=[x for x in lines if '[NSC:R248]' in x and m in x]
    print(f'{m.replace(" ","_")}={len(hits)}')
    for x in hits[:12]: print(x)
# Summary for target lines
ids=[]
for x in lines:
    if '[NSC:R248] IDENTITY_LOOKUP' in x and 'target=1' in x:
        mm=re.search(r'identity=(\d+) result=(0x[0-9a-fA-F]+|\(nil\)|0x0)',x)
        if mm: ids.append(mm.groups())
ready=[]
for x in lines:
    if '[NSC:R248] READY_PREDICATE target=1' in x:
        mm=re.search(r'ready90=(\S+) result=(\d+)',x)
        if mm: ready.append(mm.groups())
print('TARGET_IDENTITY_RESULTS='+repr(ids[:32]))
print('TARGET_READY_RESULTS='+repr(ready[:32]))
if ids and all(r in ('0x0','(nil)') for _,r in ids):
    print('DECISION=IDENTITY_LOOKUP_NULL')
elif ids and any(r not in ('0x0','(nil)') for _,r in ids):
    if ready and all(r=='0' for _,r in ready):
        print('DECISION=POST_LOOKUP_MODEL_INIT_BLOCKER')
    elif ready and any(r=='1' for _,r in ready):
        print('DECISION=CREATE_READY_PASS')
    else:
        print('DECISION=IDENTITY_NON_NULL_NEED_READY_EVIDENCE')
else:
    print('DECISION=NO_TARGET_IDENTITY_EVENT')
