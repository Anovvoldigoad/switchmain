#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1]); lines=p.read_text(errors='replace').splitlines()
keys=('[NSC:P90A]','[NSC:P89A] ACTOR_PRED','[NSC:P59A] PLAY_CALL','[NSC:P55A] ACTION_ROUTE')
out=[x for x in lines if any(k in x for k in keys)]
for x in out: print(x)
print(f'P90_RELEVANT_LINES={len(out)}',file=sys.stderr)
