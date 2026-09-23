#!/usr/bin/env python3
from pathlib import Path
R=Path.cwd();c=(R/'overlay/source/program/nsc_cpk_bridge.cpp').read_text();h=(R/'overlay/source/program/nsc_cpk_bridge.hpp').read_text();m=(R/'overlay/source/program/main.cpp').read_text()
checks={'MAIN':m.count('nsc::InstallP87AActiveProducerProbe();')==1,'HEADER':h.count('void InstallP87AActiveProducerProbe();')==1,'MARKERS':all(x in c for x in ('[NSC:P87A] READY','[NSC:P87A] PROD','[NSC:P87A] HELPER','[NSC:P87A] ACTOR_PRED')),'TARGETS':all(x in c for x in ('0x7D3AD0','0x8B30E4','0x7E24EC')),'READONLY':all(x in c for x in ('no_bda4_write=1','no_bdc8_write=1','no_force_return=1')),'NO281':'char_id == 281' not in c and 'char_id==281' not in c}
for k,v in checks.items():print(f'P87_{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()):raise SystemExit('P87A_SOURCE_SANITY=FAIL')
print('P87A_SOURCE_SANITY=PASS')
