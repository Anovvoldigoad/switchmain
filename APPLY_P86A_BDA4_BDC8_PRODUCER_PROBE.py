#!/usr/bin/env python3
from pathlib import Path
import shutil, sys
ROOT=Path.cwd()
CPP=ROOT/'overlay/source/program/nsc_cpk_bridge.cpp'
HPP=ROOT/'overlay/source/program/nsc_cpk_bridge.hpp'
MAIN=ROOT/'overlay/source/program/main.cpp'
for p in (CPP,HPP,MAIN):
    if not p.is_file(): raise SystemExit(f'FATAL missing {p}')
cpp=CPP.read_text(); hpp=HPP.read_text(); main=MAIN.read_text()
if main.count('nsc::InstallP85AF58IntentProbe();') != 1: raise SystemExit('FATAL expected exactly one active P85 main call')
if 'InstallP86ABda4Bdc8ProducerProbe' in cpp or 'nsc::InstallP86ABda4Bdc8ProducerProbe();' in main:
    raise SystemExit('FATAL P86 already present; refusing duplicate patch')
for needle in ('[NSC:P85A] READY','P85F58IntentProbeHook','kP85F58Offset'):
    if needle not in cpp: raise SystemExit(f'FATAL missing P85 parent marker {needle}')
# backups are local recovery only; never stage them.
for p in (CPP,HPP,MAIN): shutil.copy2(p, p.with_name(p.name+'.pre_p86a'))
BLOCK = Path(__file__).with_name('P86_CPP_BLOCK.txt').read_text()
pos=cpp.rfind('} // namespace nsc')
if pos < 0: raise SystemExit('FATAL namespace nsc terminator not found')
cpp=cpp[:pos]+BLOCK+'\n'+cpp[pos:]
CPP.write_text(cpp)
if 'void InstallP85AF58IntentProbe();' not in hpp: raise SystemExit('FATAL P85 header declaration absent')
hpp=hpp.replace('void InstallP85AF58IntentProbe();','void InstallP85AF58IntentProbe();\nvoid InstallP86ABda4Bdc8ProducerProbe();',1)
HPP.write_text(hpp)
main=main.replace('nsc::InstallP85AF58IntentProbe();','nsc::InstallP86ABda4Bdc8ProducerProbe();',1)
main=main.replace('NSC P85A F58 intent probe exception','NSC P86A BDA4 BDC8 producer probe exception')
MAIN.write_text(main)
print('P86A_SOURCE_PATCH=PASS')
