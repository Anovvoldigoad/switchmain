#!/usr/bin/env python3
import re,sys
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
lines=open(p,errors='replace').read().splitlines()
ready=[x for x in lines if '[NSC:P98B] READY' in x]
req=[x for x in lines if '[NSC:P98B] STATE_REQ' in x]
r125=[x for x in req if re.search(r'\breq=125\b',x)]
a708=[x for x in req if re.search(r'\baction=708(?:->|\b)',x)]
e9c125=[x for x in lines if ('[NSC:P93A] CORE' in x or '[NSC:P95A] QUEUECTRL' in x) and re.search(r'\be9c=(?:125|0000007d)\b',x,re.I)]
print('P98B_READY',len(ready))
print('STATE_REQ',len(req),'REQ125',len(r125),'ACTION708_REQ',len(a708),'EXISTING_E9C125',len(e9c125))
if ready: print(ready[0])
print('\n=== req=125 ===')
for x in r125[:20]: print(x)
if r125:
    print('\nDECISION: BASE_VSLOT_WRITER_HIT — use caller_off/call_m4 as exact state125 producer.')
elif e9c125:
    print('\nDECISION: BASE_VSLOT_MISS — E9C=125 still occurred; pivot to direct/non-virtual writer (0x7A8A9C family).')
else:
    print('\nDECISION: no state125 observed in this run; reproduce through native 708 failure window.')
