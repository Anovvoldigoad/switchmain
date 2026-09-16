#!/usr/bin/env python3
import re, sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {Path(sys.argv[0]).name} uzuy_log.txt")
text = Path(sys.argv[1]).read_text(errors='replace')
lines = [ln for ln in text.splitlines() if '[NSC:P30]' in ln]
for ln in lines:
    print(ln)

print('\n=== P30 SUMMARY ===')
ready=[x for x in lines if '] READY ' in x]
chars=[x for x in lines if '] CHAR ' in x]
req=[x for x in lines if '] LOAD_REQ ' in x]
create=[x for x in lines if '] LOAD_CREATE ' in x]
status=[x for x in lines if '] LOAD_STATUS ' in x]
chunks=[x for x in lines if '] CHUNK ' in x]
print('p30_lines=',len(lines),'LOAD_REQ=',len(req),'LOAD_CREATE=',len(create),'LOAD_STATUS=',len(status),'CHUNK=',len(chunks))

if not ready:
    print('CLASS=NO_READY: P30 did not initialize or log was not captured.')
    raise SystemExit(0)
if not any('cpk=1' in x and 'trace=1' in x for x in ready):
    print('CLASS=HOOK_FAIL: inspect READY/fingerprint lines before interpreting resource data.')
    raise SystemExit(0)
if not any('id=281' in x and 'code=mtob' in x for x in chars):
    print('CLASS=BASELINE_CONTAMINATION: expected fixture ID281->mtob was not observed.')
    raise SystemExit(0)

null_re=re.compile(r'result=(?:0x0+|\(nil\)|null|nullptr)\b',re.I)
misses=[x for x in chunks if null_re.search(x)]
if misses:
    print('CLASS=CHILD_CHUNK_MISS')
    print('FIRST_MISS=',misses[0])
    print('NEXT=Use the exact path/key from FIRST_MISS; do not add unrelated assets.')
    raise SystemExit(0)

sts=[]
for x in status:
    m=re.search(r'path=(.*?) status=(\d+)',x)
    if m:
        sts.append((m.group(1),int(m.group(2)),x))
for code,label in [(4,'CHILD_NOT_IN_FILELOAD_LIST'),(5,'CHILD_NATIVE_LOAD_ERROR')]:
    bad=[x for p,s,x in sts if s==code and 'prm_load' not in p]
    if bad:
        print('CLASS='+label)
        print('FIRST_BAD_STATUS=',bad[0])
        raise SystemExit(0)

if chunks:
    print('CLASS=NO_CUSTOM_CHUNK_MISS_SEEN')
    print('All captured custom CHUNK calls were non-null. If preview/VS still fails, move downstream to row consumer/actor construction.')
else:
    print('CLASS=NO_CUSTOM_CHUNK_CALLS')
    print('Custom manifest loaded but ccGetChunkBinary did not receive a captured custom path/key; next trace should target the prm_load row consumer itself.')
