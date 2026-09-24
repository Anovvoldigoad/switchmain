#!/usr/bin/env python3
import sys,re
from pathlib import Path
if len(sys.argv)!=2:
 print('usage: analyze_p101a_log.py <uzuy_log.txt>'); raise SystemExit(2)
s=Path(sys.argv[1]).read_text(errors='replace')
ready=[x for x in s.splitlines() if '[NSC:P101A] READY' in x]
hold=[x for x in s.splitlines() if '[NSC:P101A] HOLD125' in x]
op23=[x for x in s.splitlines() if '[NSC:P101A] OP23 ' in x]
op23r=[x for x in s.splitlines() if '[NSC:P101A] OP23_RESULT' in x]
pass125=[x for x in s.splitlines() if '[NSC:P101A] PASS125' in x]
play710=[x for x in s.splitlines() if ('index=710' in x or 'code=710' in x) and 'char=281' in x]
play708=[x for x in s.splitlines() if ('index=708' in x or 'code=708' in x) and 'char=281' in x]
print('ready',len(ready)); print('custom708',len(play708)); print('hold125',len(hold)); print('op23',len(op23)); print('op23_result',len(op23r)); print('pass125',len(pass125)); print('custom710',len(play710))
for title,arr in [('READY',ready),('FIRST_HOLD125',hold[:3]),('OP23',op23[:3]),('OP23_RESULT',op23r[:3]),('PASS125',pass125[:3]),('CUSTOM710',play710[:8])]:
 print('\n['+title+']')
 for x in arr: print(x)
if play710 and op23:
 print('\nP101A_RESULT=STRONG_PASS_EVENT_DRIVEN_710')
elif hold and not op23 and pass125:
 print('\nP101A_RESULT=FAIL_OPEN_NO_OP23')
elif hold and not op23:
 print('\nP101A_RESULT=HOLD_ACTIVE_NO_OP23_OBSERVED')
else:
 print('\nP101A_RESULT=NO_DECISIVE_HOLD')
