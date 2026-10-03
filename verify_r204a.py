from pathlib import Path
import sys
root=Path(__file__).resolve().parent
core=(root/'overlay/source/program/nsc_runtime_core.cpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
checks={
 'core_calls_r204a_only': 'return nsc::InstallR204ANativeMtobTrace();' in core,
 'no_gameplay_installer_in_core': all(x not in core for x in ['InstallP128','InstallR172','InstallR175','InstallR176','InstallR177','InstallV2N','InstallV2P','InstallResolverHookMigrationProbe','InstallOriginalMainRuntimePatches']),
 'public_decl': 'bool InstallR204ANativeMtobTrace();' in hpp,
 'ready_marker': '[NSC:R204A] READY' in bridge,
 'load_req': '[NSC:R204A] LOAD_REQ' in bridge,
 'load_create': '[NSC:R204A] LOAD_CREATE' in bridge,
 'load_status': '[NSC:R204A] LOAD_STATUS' in bridge,
 'file_open': '[NSC:R204A] FILE_OPEN' in bridge,
 'process': '[NSC:R204A] PROCESS' in bridge,
 'chunk': '[NSC:R204A] CHUNK' in bridge,
 'mtob_fallback': 'BoundedContains(path, "mtob"' in bridge,
 'no_cpk_bind_install_in_r204a': 'CpkBindHook::Install' not in bridge[bridge.index('bool InstallR204ANativeMtobTrace()'):bridge.index('bool InstallPlayActionProbe()')],
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
print('R204A_SOURCE_VERIFY=PASS')
