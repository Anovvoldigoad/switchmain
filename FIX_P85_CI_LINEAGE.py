#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

HERE = Path(__file__).resolve().parent
ROOT = Path.cwd()
if not (ROOT / '.github' / 'workflows').exists():
    alt = Path('/storage/emulated/0/Downloads')
    if (alt / '.github' / 'workflows').exists(): ROOT = alt
    else: raise SystemExit('ERROR: run from repository root; .github/workflows not found')

wfdir = ROOT / '.github' / 'workflows'
old = []
for p in sorted(list(wfdir.glob('*.yml')) + list(wfdir.glob('*.yaml'))):
    t = p.read_text()
    if 'verify_p83a_kit.py' in t or 'P83A' in t or 'p83a' in p.name.lower():
        old.append(p)

if not old:
    raise SystemExit('ERROR: no P83 workflow found; refusing blind CI edit')

# Historical P83 workflows remain available manually, but must stop firing on push.
for p in old:
    t = p.read_text()
    before = t
    # Only remove the standard top-level two-space push trigger used by this repo lineage.
    t = t.replace('  push:\n', '', 1)
    if t == before and 'workflow_dispatch:' not in t:
        raise SystemExit(f'ERROR: could not safely make {p} manual-only')
    p.write_text(t)
    print(f'P83_MANUAL_ONLY={p.relative_to(ROOT)}')

# Install current verifier/support files and current automatic workflow.
for name in ['verify_p85a_source.py','README_P85A.txt','analyze_p85a_log.py']:
    src = HERE / name
    if not src.exists(): raise SystemExit(f'ERROR: missing {src}')
    dst = ROOT / name
    if src.resolve() != dst.resolve(): shutil.copy2(src, dst)
    print(f'INSTALLED={dst.relative_to(ROOT)}')

srcwf = HERE / '.github' / 'workflows' / 'build-subsdk9-p85a.yml'
dstwf = wfdir / 'build-subsdk9-p85a.yml'
if not srcwf.exists():
    raise SystemExit(f'ERROR: missing {srcwf}')
if srcwf.resolve() != dstwf.resolve():
    shutil.copy2(srcwf, dstwf)
    print(f'INSTALLED={dstwf.relative_to(ROOT)}')
else:
    print(f'ALREADY_INSTALLED={dstwf.relative_to(ROOT)}')

# Fail closed on active source lineage.
main=(ROOT/'overlay/source/program/main.cpp').read_text()
cpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
assert main.count('nsc::InstallP85AF58IntentProbe();') == 1, 'P85 active main missing/duplicate'
assert 'nsc::InstallP84AIntentDiscriminator();' not in main, 'P84 still directly active in main'
assert '[NSC:P85A] READY' in cpp, 'P85 source marker missing'
assert 'InstallP84AIntentDiscriminator();' in cpp, 'P85 parent P84 installation missing'

print('P85_CI_LINEAGE_FIX=PASS')
print('NEXT: python3 verify_p85a_source.py && git diff --check && git status --short')
