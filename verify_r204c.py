#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(__file__).resolve().parent
core=(root/'overlay/source/program/nsc_runtime_core.cpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
checks={
 'core_calls_r204c_only': 'return nsc::InstallR204CNativeMtobProcessTrace();' in core,
 'no_gameplay_installer_in_core': all(x not in core for x in ['InstallP128','InstallR172','InstallR175','InstallR176','InstallR177','InstallV2N','InstallV2P','InstallResolverHookMigrationProbe','InstallOriginalMainRuntimePatches']),
 'public_decl': 'bool InstallR204CNativeMtobProcessTrace();' in hpp,
 'ready_marker': '[NSC:R204C] READY' in bridge,
 'load_req': '[NSC:R204C] LOAD_REQ' in bridge,
 'load_create': '[NSC:R204C] LOAD_CREATE' in bridge,
 'load_status': '[NSC:R204C] LOAD_STATUS' in bridge,
 'file_open': '[NSC:R204C] FILE_OPEN' in bridge,
 'process': '[NSC:R204C] PROCESS' in bridge,
 'chunk': '[NSC:R204C] CHUNK' in bridge,
 'process_offset_fixed': 'kLoadRequestProcessOffset = 0x116F404' in bridge,
 'old_process_offset_absent': 'kLoadRequestProcessOffset = 0x106F404' not in bridge,
 'process_mandatory': 'LogFingerprintFail("R204C_PROCESS", kLoadRequestProcessOffset); ok = false;' in bridge and 'LoadRequestProcessHook::InstallAtOffset(kLoadRequestProcessOffset);' in bridge,
 'process_fingerprint_present': all(x in bridge for x in ['0xA9BC7BFD','0xA9015FF8','0xA90257F6','0xA9034FF4','0xD10A03FF','0xD0019008','0xB9807058','0xAA0003F5']),
 'mtob_fallback': 'BoundedContains(path, "mtob"' in bridge,
 'no_cpk_bind_install_in_r204c': 'CpkBindHook::Install' not in bridge[bridge.index('bool InstallR204CNativeMtobProcessTrace()'):bridge.index('bool InstallPlayActionProbe()')],
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
print('R204C_SOURCE_VERIFY=PASS')
