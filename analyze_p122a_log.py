#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
s=p.read_text(errors='replace')
ready=re.findall(r'\[NSC:P122A\] READY[^\n]*',s)
gates=re.findall(r'\[NSC:P120A\] GATE[^\n]*',s)
custom710=[x for x in s.splitlines() if 'code=710' in x and ('char=281' in x or re.search(r'char=(?:28[1-9]|29\d|[3-9]\d\d|\d{4,})',x))]
print('P122_READY',ready[-1] if ready else 'MISSING')
print('P120_GATES',len(gates))
for x in gates: print(x)
print('CUSTOM_710_ROWS',len(custom710))
for x in custom710[:20]: print(x)
