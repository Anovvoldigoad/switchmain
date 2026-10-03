#!/usr/bin/env python3
import sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else "uzuy_log.txt")
text=p.read_text(errors="replace")
markers=["[NSC:R204G] READY","mtobprm_load.bin.xfbin","mtobcharsel.xfbin","[NSC:R204G] RESOURCE_LOOKUP","[NSC:R204G] CHUNK_LOW","[NSC:R204G] CHUNK","1nrtbod1","1nrtcharsel"]
for line in text.splitlines():
    if any(m in line for m in markers): print(line)
