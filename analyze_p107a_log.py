#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('uzuy_log.txt')
s=p.read_text(errors='replace').splitlines()
ready=[x for x in s if '[NSC:P107A] READY' in x]
bridge=[x for x in s if '[NSC:P107A] BRIDGE' in x]
custom710=[x for x in s if 'char=281' in x and ('index=710' in x or 'code=710' in x)]
custom261=[x for x in s if 'char=281' in x and ('index=261' in x or 'code=261' in x)]
custom74=[x for x in s if 'char=281' in x and ('index=74' in x or 'code=74' in x)]
print('ready',len(ready),'bridge',len(bridge),'custom710',len(custom710),'custom261',len(custom261),'custom74',len(custom74))
for title,arr in [('READY',ready[:1]),('BRIDGE',bridge[:8]),('CUSTOM710',custom710[:12]),('CUSTOM261',custom261[:6])]:
 print('\n['+title+']')
 for x in arr: print(x)
if bridge and custom710:
 print('\nP107A_RESULT=CANDIDATE_PASS_NATIVE_710')
elif bridge and not custom710:
 print('\nP107A_RESULT=BRIDGE_FIRED_NO_710')
elif not bridge:
 print('\nP107A_RESULT=GUARD_NOT_HIT')
