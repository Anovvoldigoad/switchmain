from pathlib import Path
import sys
root=Path(__file__).resolve().parent
core=(root/'overlay/source/program/nsc_runtime_core.cpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
checks={
 'core_calls_r204b_only': 'return nsc::InstallR204BNativeMtobTrace();' in core,
 'no_gameplay_installer_in_core': all(x not in core for x in ['InstallP128','InstallR172','InstallR175','InstallR176','InstallR177','InstallV2N','InstallV2P','InstallResolverHookMigrationProbe','InstallOriginalMainRuntimePatches']),
 'public_decl': 'bool InstallR204BNativeMtobTrace();' in hpp,
 'ready_marker': '[NSC:R204B] READY' in bridge,
 'load_req': '[NSC:R204B] LOAD_REQ' in bridge,
 'load_create': '[NSC:R204B] LOAD_CREATE' in bridge,
 'load_status': '[NSC:R204B] LOAD_STATUS' in bridge,
 'file_open': '[NSC:R204B] FILE_OPEN' in bridge,
 'process': '[NSC:R204B] PROCESS' in bridge,
 'chunk': '[NSC:R204B] CHUNK' in bridge,
 'mtob_fallback': 'BoundedContains(path, "mtob"' in bridge,
 'no_cpk_bind_install_in_r204b': 'CpkBindHook::Install' not in bridge[bridge.index('bool InstallR204BNativeMtobTrace()'):bridge.index('bool InstallPlayActionProbe()')],
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
print('R204B_SOURCE_VERIFY=PASS')
