#!/usr/bin/env python3
import re, sys
from collections import OrderedDict

if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} <uzuy_log.txt>")
    raise SystemExit(2)

lines=open(sys.argv[1], errors="replace").read().splitlines()
p31=[x for x in lines if "[NSC:P31]" in x]
req=[]; create=[]; changes=[]; chunks=[]
for line in p31:
    if " LOAD_REQ " in line:
        m=re.search(r"path=(.*?) options=", line)
        if m: req.append(m.group(1))
    elif " LOAD_CREATE " in line:
        m=re.search(r"path=(.*?) options=", line)
        if m: create.append(m.group(1))
    elif " LOAD_STATUS " in line:
        m=re.search(r"path=(.*?) first=(\d+) prev=(\d+) status=(\d+)", line)
        if m: changes.append((m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), line))
    elif " CHUNK " in line:
        chunks.append(line)

final=OrderedDict(); bad=[]
for path, first, prev, st, line in changes:
    final[path]=st
    if st in (4,5): bad.append((path, st, line))

print("=== P31 SUMMARY ===")
print(f"p31_lines={len(p31)} LOAD_REQ={len(req)} LOAD_CREATE={len(create)} STATUS_TRANSITIONS={len(changes)} CHUNK={len(chunks)}")
if any("STATUS_TABLE_OVERFLOW" in x for x in p31): print("WARNING=STATUS_TABLE_OVERFLOW")
print("\nFINAL_STATUS_BY_PATH")
for path, st in final.items(): print(f"  {st}: {path}")
print("\nBAD_STATUS_EVENTS")
if not bad: print("  none")
else:
    seen=set()
    for path, st, line in bad:
        k=(path,st)
        if k in seen: continue
        seen.add(k); print(f"  status={st} path={path}")
print("\nREQUESTED_WITHOUT_STATUS")
for path in OrderedDict.fromkeys(req):
    if path not in final: print(f"  {path}")
print("\nCHUNK_NULLS")
nulls=[x for x in chunks if re.search(r"result=(?:0x0|\(nil\)|0)$", x)]
if not nulls: print("  none")
else:
    for x in nulls: print(x)
