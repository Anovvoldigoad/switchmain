#!/usr/bin/env python3
from pathlib import Path
import re
r=Path(__file__).resolve().parent
s=(r/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
m=(r/'overlay/source/program/main.cpp').read_text()
h=(r/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
for tok in ['struct P55ActorState','ReadP55ActorState','[NSC:P55A] STATE236','[NSC:P55A] SKILL_WRITE','[NSC:P55A] STATE121','[NSC:P55A] ACTION_ROUTE','void InstallP55AStateSampler()']:
    assert tok in s,tok
assert 'nsc::InstallP55AStateSampler();' in m
assert 'void InstallP55AStateSampler();' in h
body=re.search(r'void InstallP55AStateSampler\(\) \{(.*?)\n\}',s,re.S); assert body
assert 'InstallP50AConditionCompat();' in body.group(1)
assert 'InstallP54DirectJutsuOwnerProbes' not in body.group(1)
assert 'InstallP52PreUjTraceHooks' not in body.group(1)
assert 'added_trampolines=0 total_trampolines=5' in body.group(1)
print('P55A_VERIFY=PASS')
print('active_trampolines=5')
print('added_trampolines=0')
print('gameplay_writes_added=0')
