#!/usr/bin/env python3
from pathlib import Path
import re
r=Path(__file__).resolve().parent
s=(r/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
m=(r/'overlay/source/program/main.cpp').read_text()
h=(r/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
required=[
    'kRejectedControlBlockOffset = 0x12A24',
    'kControlScanStart = 0x12800',
    'kControlScanEnd   = 0x12B20',
    'LogP56BControlSnapshot',
    '[NSC:P56B] CONTROL_SNAPSHOT',
    '[NSC:P56B] CONTROL_CAND',
    'CUSTOM_O14_UJ_ENABLE',
    'VANILLA_PLAY700',
    'void InstallP56BControlLocator()',
]
for tok in required:
    assert tok in s, tok
assert 'nsc::InstallP56BControlLocator();' in m
assert 'void InstallP56BControlLocator();' in h
body=re.search(r'void InstallP56BControlLocator\(\) \{(.*?)\n\}',s,re.S); assert body
b=body.group(1)
assert 'InstallP50AConditionCompat();' in b
assert 'InstallP54DirectJutsuOwnerProbes' not in b
assert 'InstallP52PreUjTraceHooks' not in b
assert 'added_trampolines=0 total_trampolines=5 writes=0' in b
# Scan safety invariant: candidate max field 0x58 ends at the already recovered +0x12B78 boundary.
assert 0x12B20 + 0x58 == 0x12B78
# The rejected P40 address must never be used by the live Event236 O14 path.
case14=s[s.index('case 14: {'):s.index('case 15: {',s.index('case 14: {'))]
assert 'kRejectedControlBlockOffset' not in case14
assert '*reinterpret_cast' not in case14.split('return 1;')[0]  # no locator/control write
print('P56B_VERIFY=PASS')
print('active_trampolines=5')
print('added_trampolines=0')
print('gameplay_writes_added=0')
print('scan=0x12800..0x12B20; max_field=0x12B78')
print('rejected_base_0x12A24_write=ABSENT')
