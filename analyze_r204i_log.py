#!/usr/bin/env python3
import sys,re
from pathlib import Path
p=Path(sys.argv[1])
s=p.read_text(errors="replace").splitlines()
for tag in ("OWNER_INIT","OWNER_READY","OWNER_STATE","RESOURCE_LOOKUP","CHUNK_LOW"):
    rows=[x for x in s if f"[NSC:R204I] {tag}" in x and "charsel" in x]
    print(f"{tag}_CHARSEL_COUNT={len(rows)}")
    for x in rows[:80]: print(x)
