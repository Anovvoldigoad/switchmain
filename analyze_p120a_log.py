#!/usr/bin/env python3
import re,sys
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
s=open(p,errors='replace').read().splitlines()
ready=[x for x in s if '[NSC:P120A] READY' in x]
gates=[x for x in s if '[NSC:P120A] GATE' in x]
bridges=[x for x in gates if 'bridge=1' in x]
a710=[x for x in s if ('[NSC:P91A] HANDOFF' in x or '[NSC:P59A] PLAY_CALL' in x or '[NSC:P93A] CORE' in x) and re.search(r'(?:index|code|action)=710\b',x)]
p116=[x for x in s if '[NSC:P116A]' in x]
print('P120_READY',len(ready))
if ready: print(ready[-1])
print('P120_GATE_ROWS',len(gates))
print('P120_BRIDGE_ROWS',len(bridges))
for x in bridges: print(x)
print('ACTION710_EVIDENCE',len(a710))
for x in a710[:20]: print(x)
print('P116_ROWS',len(p116))
if ready and 'patch_ok=1' in ready[-1] and bridges:
    print('P120_PATCH_TRIGGERED=YES')
elif ready and 'patch_ok=1' in ready[-1]:
    print('P120_PATCH_TRIGGERED=NO')
else:
    print('P120_DEPLOYMENT_INVALID_OR_MISSING')
