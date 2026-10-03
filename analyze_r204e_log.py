#!/usr/bin/env python3
import sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else "uzuy_log.txt")
text=p.read_text(errors="replace")
markers=["[NSC:R204E] READY","mtobprm_load.bin.xfbin","mtobcharsel.xfbin","[NSC:R204E] RESOURCE_LOOKUP","[NSC:R204E] CHUNK_LOW","[NSC:R204E] CHUNK"]
for line in text.splitlines():
    if any(m in line for m in markers): print(line)
