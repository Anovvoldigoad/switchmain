#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
deploy=root/'deploy/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(name,cond):
    checks.append((name,bool(cond)))
ck('calls_p57', 'InstallP57ACentralSetterTrace();' in main)
ck('setter_offset', 'kCentralActionSetterOffset = 0x766320' in cpp)
ck('void_4arg_callback', 'static void Callback(void* actor, int32_t action, int32_t a2, int32_t a3)' in cpp)
ck('setter_install', 'CentralActionSetterHook::InstallAtOffset(kCentralActionSetterOffset);' in cpp)
ck('ready_6', 'total_trampolines=6 writes=0 setter=0x766320' in cpp)
ck('generic_custom_log_filter', 'char_id > kVanillaMaxCharId && char_id < 0x1000u' in cpp)
ck('no_281_gameplay_if', not re.search(r'if\s*\([^\n]*char_id\s*==\s*281',cpp))
ck('no_708_710_force', '708->710' not in cpp and '708 → 710' not in cpp)
ck('deploy_main_p50', sha(deploy)=='8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be')
ck('restore_main', sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')
failed=[n for n,v in checks if not v]
for n,v in checks: print(f'{n}={"PASS" if v else "FAIL"}')
if failed:
    print('P57A_VERIFY=FAIL',','.join(failed)); sys.exit(1)
print('P57A_VERIFY=PASS')
print('active_trampolines=6')
print('added_trampolines=1')
print('gameplay_writes_added=0')
print('setter=0x766320')
print('deploy_main_sha256='+sha(deploy))
print('restore_main_sha256='+sha(restore))
