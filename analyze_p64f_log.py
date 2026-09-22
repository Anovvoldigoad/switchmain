#!/usr/bin/env python3
from pathlib import Path
import re, sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
s=p.read_text(errors='replace')
patterns={
 'ready': r'\[NSC:P64F\] READY',
 'sem_enable': r'\[NSC:P64F\] UJ_SEM_SET .*enabled=1',
 'sem_disable': r'\[NSC:P64F\] UJ_SEM_SET .*enabled=0',
 'sem_gate_promote': r'\[NSC:P64F\] UJ_SEM_GATE .*native=0 semantic=1 ret=1',
 'tobi_445': r'\[NSC:P59A\] PLAY_CALL .*char=281 index=445',
 'tobi_700': r'\[NSC:P59A\] PLAY_CALL .*char=281 index=700',
 'tobi_f58': r'\[NSC:P63A\] UJ_F58 .*char=281',
 'vanilla_700': r'\[NSC:P59A\] PLAY_CALL .*char=(?!281\b)\d+ index=700',
}
for k,v in patterns.items():
    print(f'{k}={len(re.findall(v,s))}')
print('\nP64F gate lines:')
for line in s.splitlines():
    if '[NSC:P64F] UJ_SEM_GATE' in line or '[NSC:P64F] UJ_SEM_SET' in line:
        print(line)
