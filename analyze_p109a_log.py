#!/usr/bin/env python3
import re,sys,collections
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
lines=open(p,errors='replace').read().splitlines()
ready=[x for x in lines if '[NSC:P109A] READY' in x]
req=[x for x in lines if '[NSC:P109A] STATE_REQ' in x]

def val(x,k):
    m=re.search(r'\b'+re.escape(k)+r'=([^ ]+)',x)
    return m.group(1) if m else '?'
print('P109_READY',len(ready))
if ready: print(ready[0])
print('STATE_REQ_ROWS',len(req))
c=collections.Counter((val(x,'char'),val(x,'side'),val(x,'req'),val(x,'caller_off')) for x in req)
print('\n=== request summary ===')
for k,n in sorted(c.items(), key=lambda z:(z[0][2],z[0][0],z[0][3])):
    print(n, 'char',k[0],'side',k[1],'req',k[2],'caller',k[3])
print('\n=== req137 rows ===')
r137=[x for x in req if re.search(r'\breq=137\b',x)]
for x in r137: print(x)
print('\n=== req125 rows ===')
for x in req:
    if re.search(r'\breq=125\b',x): print(x)
# Same-log evidence that E9C=137 existed, independent of P109 gateway.
e9c137=[x for x in lines if ('[NSC:P93A] CORE' in x or '[NSC:P81A] POLICY' in x) and re.search(r'\be9c=(?:137|00000089)\b',x,re.I)]
van_r137=[x for x in r137 if re.search(r'\bchar=(?!281\b)\d+',x)]
print('\nE9C137_EVIDENCE_ROWS',len(e9c137),'P109_VANILLA_REQ137',len(van_r137))
if van_r137:
    print('DECISION=BASE_GATEWAY_PROVEN_FOR_STATE137')
    print('NEXT=use vanilla req137 caller_off as exact producer; compare producer conditions against custom action708')
elif e9c137:
    print('DECISION=STATE137_BYPASSES_7A89A4')
    print('NEXT=probe fingerprinted direct/simple E9C setter main+0x7A8A9C')
else:
    print('DECISION=NO_NATIVE_STATE137_IN_RUN')
    print('NEXT=reproduce one successful vanilla UJ before custom attempt')
