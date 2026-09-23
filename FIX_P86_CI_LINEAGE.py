#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path.cwd(); wd=ROOT/'.github/workflows'; wd.mkdir(parents=True,exist_ok=True)
# Historical P85 stays available manually but must not own push automation.
for p in sorted(wd.glob('*p85*.yml'))+sorted(wd.glob('*p85*.yaml')):
    s=p.read_text()
    # remove a top-level bare push: line while preserving workflow_dispatch
    ns=re.sub(r'(?m)^  push:\s*\n','',s)
    if ns!=s: p.write_text(ns)
    print(f'P85_MANUAL_ONLY={p.relative_to(ROOT)}')
# Install/refresh the current P86 workflow from the extracted kit reference.
src=ROOT/'build-subsdk9-p86a.yml'; dst=wd/'build-subsdk9-p86a.yml'
if not src.is_file(): raise SystemExit('FATAL missing build-subsdk9-p86a.yml from kit')
if src.resolve()!=dst.resolve(): dst.write_text(src.read_text())
else: print(f'ALREADY_INSTALLED={dst.relative_to(ROOT)}')
if not dst.is_file(): raise SystemExit('FATAL P86 workflow install failed')
print(f'INSTALLED={dst.relative_to(ROOT)}')
print('P86_CI_LINEAGE_FIX=PASS')
