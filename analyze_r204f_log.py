#!/usr/bin/env python3
import sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else "uzuy_log.txt")
text=p.read_text(errors="replace")
markers=["[NSC:R204F] READY","mtobprm_load.bin.xfbin","mtobcharsel.xfbin","[NSC:R204F] RESOURCE_LOOKUP","[NSC:R204F] CHUNK_LOW","[NSC:R204F] CHUNK"]
for line in text.splitlines():
    if any(m in line for m in markers): print(line)
