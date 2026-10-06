#!/usr/bin/env python3
import re, sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: analyze_p32_log.py <uzuy_log.txt>")

lines = Path(sys.argv[1]).read_text(errors="replace").splitlines()
p32 = [x for x in lines if "[NSC:P32]" in x]

opens = []
process = []
status = []
chunks = []
for line in p32:
    if " FILE_OPEN " in line:
        m = re.search(r"path=(.*?) slot=(\d+) result=(\d+)", line)
        if m: opens.append((m.group(1), int(m.group(2)), int(m.group(3)), line))
    elif " PROCESS " in line:
        m = re.search(r"path=(.*?) owner=.*? status=(\d+) readerr=(\d+)", line)
        if m: process.append((m.group(1), int(m.group(2)), int(m.group(3)), line))
    elif " LOAD_STATUS " in line:
        m = re.search(r"path=(.*?) first=(\d+) prev=(\d+) status=(\d+)", line)
        if m: status.append((m.group(1), int(m.group(4)), line))
    elif " CHUNK " in line:
        chunks.append(line)

print("=== P32 SUMMARY ===")
print(f"p32_lines={len(p32)} FILE_OPEN={len(opens)} PROCESS={len(process)} STATUS={len(status)} CHUNK={len(chunks)}")

print("\nOPEN_FAILURES")
bad_open = [x for x in opens if x[2] == 0]
if bad_open:
    for path, slot, result, _ in bad_open:
        print(f"  result={result} slot={slot} path={path}")
else:
    print("  none")

print("\nPROCESS_STATUS5")
bad_proc = [x for x in process if x[1] == 5]
if bad_proc:
    for path, st, err, _ in bad_proc:
        print(f"  status={st} readerr={err} path={path}")
else:
    print("  none")

print("\nCLASSIFICATION")
paths = sorted(set([x[0] for x in opens] + [x[0] for x in process]))
for path in paths:
    os_ = [x for x in opens if x[0] == path]
    ps_ = [x for x in process if x[0] == path]
    if any(x[2] == 0 for x in os_):
        cls = "OPEN_FAIL"
    elif any(x[1] == 5 and x[2] == 1 for x in ps_):
        cls = "XFBIN_READ_FAIL"
    elif any(x[1] == 5 for x in ps_):
        cls = "PROCESS_FAIL_OTHER"
    elif any(x[1] == 2 for x in ps_):
        cls = "LOADED"
    else:
        cls = "INCOMPLETE"
    print(f"  {cls}: {path}")

print("\nCHUNK_NULLS")
nulls = [x for x in chunks if re.search(r"result=(?:0x0|\\(nil\\)|0)(?:\\s|$)", x)]
if nulls:
    for x in nulls: print(" ", x)
else:
    print("  none")
