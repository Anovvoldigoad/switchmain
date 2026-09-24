#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
s=p.read_text(errors='replace')
lines=s.splitlines()
patterns={
 'READY':r'\[NSC:P102A\] READY',
 'HOLD74':r'\[NSC:P102A\] HOLD74',
 'FAILOPEN74':r'\[NSC:P102A\] FAILOPEN74',
 'CUSTOM710':r'char=281 .*index=710 .*caller_off=0x7e6ec8',
 'CUSTOM74_798F34':r'char=281 .*index=74 .*caller_off=0x798f34',
 'CUSTOM261':r'char=281 .*index=261',
 'CUSTOM708':r'char=281 .*index=708',
}
for k,pat in patterns.items():
    hits=[x for x in lines if re.search(pat,x,re.I)]
    print(k,len(hits))
    for x in hits[:8]: print(' ',x)
print('\nDECISION')
hold=sum(bool(re.search(patterns['HOLD74'],x,re.I)) for x in lines)
fopen=sum(bool(re.search(patterns['FAILOPEN74'],x,re.I)) for x in lines)
uj710=sum(bool(re.search(patterns['CUSTOM710'],x,re.I)) for x in lines)
f74=sum(bool(re.search(patterns['CUSTOM74_798F34'],x,re.I)) for x in lines)
if uj710:
    print('NATIVE_710_REACHED_AFTER_FALLBACK74_SUPPRESSION')
elif hold and fopen:
    print('HOLD74_TRIGGERED_BUT_BOUNDED_FAILOPEN_REACHED_NO_710')
elif hold and not f74:
    print('HOLD74_TRIGGERED_NO_NATIVE_798F34_74_OBSERVED_BUT_NO_710_YET')
elif not hold:
    print('P102_GATE_DID_NOT_MATCH_RECHECK_RUNTIME_FINGERPRINT')
else:
    print('UNRESOLVED')
