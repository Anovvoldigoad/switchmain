#!/usr/bin/env python3
import sys
from pathlib import Path
text=Path(sys.argv[1]).read_text(errors="replace")
for tag in ["OWNER_TREE_VERIFY","REGISTRY_PROCESS","TARGET_REGISTRY_OWNER_READY"]:
 lines=[x for x in text.splitlines() if f"[NSC:R204L] {tag}" in x]
 print(tag, len(lines))
 for x in lines[:40]: print(x)
