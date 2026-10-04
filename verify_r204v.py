#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parent
CPP=ROOT/'overlay/source/program/nsc_cpk_bridge.cpp'
CORE=ROOT/'overlay/source/program/nsc_runtime_core.cpp'
HPP=ROOT/'overlay/source/program/nsc_cpk_bridge.hpp'
WF=ROOT/'.github/workflows/build-runtime-r181.yml'
MAIN=ROOT/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
checks=[]
def ck(name, cond):
    checks.append((name,bool(cond)))
    print(f'{name}=' + ('PASS' if cond else 'FAIL'))
cpp=CPP.read_text(); core=CORE.read_text(); hpp=HPP.read_text(); wf=WF.read_text()
ck('core_r204v_only', 'InstallR204VCharselStateGateTrace()' in core and 'InstallR204JNativeCharselOwnerTrace()' not in core)
ck('public_decl', 'bool InstallR204VCharselStateGateTrace();' in hpp)
ck('gate_offset', 'kCharsel3DStateGateOffset      = 0x549804' in cpp)
ck('registry_offset', 'kLoadOwnerRegistryProcessOffset = 0x1161C98' in cpp)
ck('registry_state_offset', 'kLoadOwnerRegistryStateOffset  = 0x1161D20' in cpp)
ck('owner_register_offset', 'kLoadOwnerRegisterOffset   = 0x1161B88' in cpp)
ck('gate_hook', 'HOOK_DEFINE_TRAMPOLINE(R204VCharselStateGateHook)' in cpp)
ck('registry_hook', 'HOOK_DEFINE_TRAMPOLINE(R204VRegistryProcessHook)' in cpp)
ck('registry_state_hook', 'HOOK_DEFINE_TRAMPOLINE(R204VRegistryStateHook)' in cpp)
ck('state_commit_observe', 's5c=%u->%u s6c=%u->%u advanced=%u' in cpp)
ck('ready_marker', '[NSC:R204V] READY installed=1 readonly=1 target=ccUiCharacterSelect3DModel_state_gate trampolines=4' in cpp)
ck('workflow_verify', 'python3 verify_r204v.py' in wf)
ck('workflow_artifact', 'NSC2Switch-R204V-CHARSEL-STATE-GATE-TRACE' in wf)
ck('no_main_package_comment', "test ! -e out/runtime/atmosphere/contents/0100FA10190A0000/exefs/main" in wf)
# Fingerprint clean v1.70 main directly.
if MAIN.exists():
    b=MAIN.read_bytes(); base=0x101
    def words(off,n=8): return [int.from_bytes(b[base+off+i:base+off+i+4],'little') for i in range(0,n*4,4)]
    ck('main_nso0', b[:4]==b'NSO0')
    ck('fp_gate', words(0x549804)==[0xA9BF4FFE,0xAA0003F3,0xF9405400,0xB4000260,0x94306121,0x34000220,0xF9406260,0xB40000C0])
    ck('fp_owner_register', words(0x1161B88)==[0xD10143FF,0xA90167FE,0xA9025FF8,0xA90357F6,0xA9044FF4,0xF9400008,0x2A0403F5,0x2A0303F6])
    reg=[0xF81E0FFE,0xA9014FF4,0xF9400C14,0x91008013,0x14000002,0xAA0903F4,0xEB13029F,0x540002E0]
    ck('fp_registry_process', words(0x1161C98)==reg)
    ck('fp_registry_state', words(0x1161D20)==reg)
else:
    ck('main_present', False)
ck('no_pycache', not any(p.name=='__pycache__' for p in ROOT.rglob('*')) and not any(ROOT.rglob('*.pyc')))
failed=[n for n,v in checks if not v]
if failed:
    print('R204V_SOURCE_VERIFY=FAIL ' + ','.join(failed)); sys.exit(1)
print('R204V_SOURCE_VERIFY=PASS')
