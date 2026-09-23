#!/usr/bin/env python3
from pathlib import Path
R=Path.cwd();c=(R/'overlay/source/program/nsc_cpk_bridge.cpp').read_text();h=(R/'overlay/source/program/nsc_cpk_bridge.hpp').read_text();m=(R/'overlay/source/program/main.cpp').read_text()
checks={
'MAIN':m.count('nsc::InstallP88AWideUJAdmissionTrace();')==1,
'HEADER':h.count('void InstallP88AWideUJAdmissionTrace();')==1,
'MARKERS':all(x in c for x in ('[NSC:P88A] READY','HELPER_8B30E4','INPUT_7C6074','MASK_7C5FB0','STATE2_7D5C10','GATE_78FDC0','ACTOR_7E24EC','PROD')),
'TARGETS':all(x in c for x in ('0x7D3AD0','0x8B30E4','0x7E24EC','0x7C553C','0x7C6074','0x7C5FB0','0x7D5C10','0x78FDC0')),
'FIELDS':all(x in c for x in ('0xBDA4','0xBDC8','0x116F4','0x133E0','0x133E4','0xE94','0xE98','0xE9C','0x404','0x408','0x5A0')),
'READONLY_DECL':all(x in c for x in ('readonly=1','preserve_orig=1','no_bdc8_write=1','no_force_return=1','no_force_f58=1','no_force700=1','no_char281_branch=1')),
'NO281':all(x not in c for x in ('char_id == 281','char_id==281','cid == 281','cid==281')),
'NO_P87_INSTALL':m.count('nsc::InstallP87AActiveProducerProbe();')==0,
}
for k,v in checks.items():print(f'P88_{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()):raise SystemExit('P88A_SOURCE_SANITY=FAIL')
print('P88A_SOURCE_SANITY=PASS')
