#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path.cwd()
if not (root/'overlay/source/program/nsc_cpk_bridge.cpp').exists(): root=Path('/storage/emulated/0/Downloads')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
checks={
'P85_MAIN_CHAIN': main.count('nsc::InstallP85AF58IntentProbe();')==1 and 'nsc::InstallP84AIntentDiscriminator();' not in main,
'P85_HEADER': hpp.count('void InstallP85AF58IntentProbe();')==1,
'P85_PARENT_P84': 'InstallP84AIntentDiscriminator();' in cpp and '[NSC:P84A] READY' in cpp,
'P85_MARKER': '[NSC:P85A] READY' in cpp,
'P85_F58_TARGET': 'kP85F58Offset = 0x7D3138' in cpp,
'P85_CALLER_FILTER': 'kP85F58CallerReturn = 0x7F46B8' in cpp and 'caller_off == kP85F58CallerReturn' in cpp,
'P85_NATIVE_RETURN': 'const uint32_t ret = Orig(actor, mode, context);' in cpp and 'return ret;' in cpp,
'P85_FINGERPRINT': '0xFC1C0FE8' in cpp and '0xF947AD08' in cpp,
'P85_NO_281_BRANCH': 'char_id == 281' not in cpp[cpp.find('// P85A — read-only'):],
'P85_NO_FORCE700': 'return 700' not in cpp[cpp.find('// P85A — read-only'):],
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
print('P85A_SOURCE_SANITY=PASS')
