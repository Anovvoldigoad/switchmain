#!/usr/bin/env python3
from pathlib import Path
R=Path.cwd(); cpp=(R/'overlay/source/program/nsc_cpk_bridge.cpp').read_text(); h=(R/'overlay/source/program/nsc_cpk_bridge.hpp').read_text(); m=(R/'overlay/source/program/main.cpp').read_text()
checks={
'P86_MAIN_CHAIN': m.count('nsc::InstallP86ABda4Bdc8ProducerProbe();')==1 and m.count('nsc::InstallP85AF58IntentProbe();')==0,
'P86_HEADER': h.count('void InstallP86ABda4Bdc8ProducerProbe();')==1,
'P86_PARENT_P85': cpp.count('InstallP85AF58IntentProbe();')>=1 and '[NSC:P85A] READY' in cpp,
'P86_MARKERS': all(x in cpp for x in ('[NSC:P86A] READY','[NSC:P86A] STATE','[NSC:P86A] CTRL','[NSC:P86A] INPUT_PRED','[NSC:P86A] ACTOR_PRED')),
'P86_TARGETS': all(x in cpp for x in ('0x11F080','0x7C6074','0x7E24EC','0x11F22C','0x11F338','0x11F23C','0x11F348')),
'P86_READONLY': 'no_bda4_write=1' in cpp and 'no_bdc8_write=1' in cpp and 'no_force_return=1' in cpp,
'P86_NO_281_BRANCH': 'char_id == 281' not in cpp and 'char_id==281' not in cpp,
'P86_NO_FORCE700': 'requested = 700' not in cpp and 'requested=700' not in cpp,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): raise SystemExit('P86A_SOURCE_SANITY=FAIL')
print('P86A_SOURCE_SANITY=PASS')
