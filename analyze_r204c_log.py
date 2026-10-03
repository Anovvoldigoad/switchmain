#!/usr/bin/env python3
import re,sys
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit('usage: python3 analyze_r204c_log.py <uzuy_log.txt>')
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
events=[x for x in lines if '[NSC:R204C]' in x]
print(f'R204C_LINES={len(events)}')
ready=[x for x in events if ' READY ' in x]
print('READY='+('PASS' if any('installed=1' in x and 'process_installed=1' in x for x in ready) else 'MISSING_OR_FAIL'))
for kind in ['LOAD_REQ','LOAD_CREATE','LOAD_STATUS','FILE_OPEN','PROCESS','CHUNK']:
    arr=[x for x in events if f'] {kind} ' in x]
    print(f'{kind}_COUNT={len(arr)}')
rx=re.compile(r'LOAD_STATUS .*?path=(\S+).*?status=(\d+)')
status={}
for x in events:
    m=rx.search(x)
    if m: status.setdefault(m.group(1),[]).append(int(m.group(2)))
for p,ss in status.items():
    if 4 in ss or 5 in ss:
        print(f'FAIL_PATH={p} STATUSES={ss}')
for x in events:
    if ' FILE_OPEN ' in x and ' result=0' in x:
        print('FIRST_FILE_OPEN_FAIL='+x); break
for x in events:
    if ' PROCESS ' in x and ('status=5' in x or re.search(r'readerr=(?!0\b)\d+',x)):
        print('FIRST_PROCESS_FAIL='+x); break
for x in events:
    if ' CHUNK ' in x and re.search(r'result=(?:0x0|\(nil\)|0|null)\b',x,re.I):
        print('FIRST_NULL_CHUNK='+x); break
focus=[x for x in events if 'mtob' in x.lower()]
print(f'MTOB_EVENT_COUNT={len(focus)}')
for x in focus[:320]: print(x)
