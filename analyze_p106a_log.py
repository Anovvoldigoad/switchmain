#!/usr/bin/env python3
from pathlib import Path
import re,sys
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('uzuy_log.txt')
lines=p.read_text(errors='replace').splitlines()
ready=[x for x in lines if '[NSC:P106A] READY' in x]
ctrl=[x for x in lines if '[NSC:P106A] CTRL520' in x]
state=[x for x in lines if '[NSC:P106A] STATE520' in x]
van710=[x for x in lines if 'caller_off=0x7e6ec8' in x.lower() and ('index=710' in x or 'code=710' in x)]
custom520=[x for x in ctrl if 'char=281' in x and ('action=708->' in x or '->708' in x)]
custom710=[x for x in lines if 'char=281' in x and ('index=710' in x or 'code=710' in x)]
print('ready',len(ready)); print('ctrl520_rows',len(ctrl)); print('state520_rows',len(state))
print('vanilla710_from_7e6ec8',len(van710)); print('custom708_ctrl520_rows',len(custom520)); print('custom710',len(custom710))
for title,arr in [('READY',ready[:2]),('CUSTOM_520',custom520[:12]),('CUSTOM_710',custom710[:12]),('VANILLA_710',van710[:8])]:
 print('\n['+title+']'); [print(x) for x in arr]
if custom520 and custom710:
 print('\nP106A_RESULT=CUSTOM_ENTERS_520_AND_REACHES_710')
elif custom520:
 print('\nP106A_RESULT=CUSTOM_ENTERS_520_BUT_NO_710__TRACE_FIRST_INTERNAL_DIVERGENCE')
elif ready:
 print('\nP106A_RESULT=NO_CUSTOM_520_ENTRY__TARGET_UPSTREAM_DISPATCH_TO_488B28')
else:
 print('\nP106A_RESULT=NO_READY')
