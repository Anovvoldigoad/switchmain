#!/usr/bin/env python3
from pathlib import Path
import struct, sys
try:
    import lz4.block
except Exception:
    lz4=None
r=Path(__file__).resolve().parent
b=(r/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
h=(r/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
c=(r/'overlay/source/program/nsc_runtime_core.cpp').read_text()
checks={
 'core_calls_r204m_only':'return nsc::InstallR204MFullPreviewPipelineTrace();' in c,
 'no_gameplay_installer_in_core':all(x not in c for x in ['InstallP128','InstallR172','InstallR175','InstallR176','InstallR177','InstallV2N','InstallV2P','InstallResolverHookMigrationProbe','InstallOriginalMainRuntimePatches']),
 'public_decl':'bool InstallR204MFullPreviewPipelineTrace();' in h,
 'ready_marker':'[NSC:R204M] READY' in b and 'registry_process_trace=1' in b and 'tree_verify=1' in b,
 'owner_tree_verify':'[NSC:R204M] OWNER_TREE_VERIFY' in b and 'same_owner=%u' in b,
 'registry_process':'[NSC:R204M] REGISTRY_PROCESS' in b,
 'target_scan':'[NSC:R204M] TARGET_REGISTRY_OWNER_READY' in b,
 'generic_bod1_path_trace':'data/spc/bod1' in b,
 'generic_bod1_key_trace':'BoundedContains(key, "bod1", 256, 4)' in b,
 'generic_bod1_ready_flag':'generic_bod1_trace=1' in b,
 'read_dispatch_offset':'kFileReadDispatchOffset   = 0x11705F0' in b,
 'read_dispatch_hook':'HOOK_DEFINE_TRAMPOLINE(FileReadDispatchHook)' in b and 'FileReadDispatchHook::InstallAtOffset(kFileReadDispatchOffset);' in b,
 'read_dispatch_markers':'[NSC:R204M] READ_DISPATCH_ENTER' in b and '[NSC:R204M] READ_DISPATCH_EXIT' in b and 'method_off=0x%lx' in b,
 'request_path_tracking':'TrackRequestPath(request, path);' in b and 'LookupRequestPath(request, path, sizeof(path))' in b,
 'read_dispatch_ready_flag':'read_dispatch_trace=1' in b and 'READ_DISPATCH' in b,
 'process_enter_exit':'[NSC:R204M] PROCESS_ENTER' in b and '[NSC:R204M] PROCESS_EXIT' in b,
 'read_stage_trace':'kReadStageOffset          = 0x120A860' in b and '[NSC:R204M] READ_STAGE_ENTER' in b and '[NSC:R204M] READ_STAGE_EXIT' in b,
 'request_finalize_trace':'kRequestFinalizeOffset    = 0x1171080' in b and '[NSC:R204M] REQUEST_FINALIZE_ENTER' in b and '[NSC:R204M] REQUEST_FINALIZE_EXIT' in b,
 'read_cleanup_trace':'kReadCleanupOffset        = 0x1170550' in b and '[NSC:R204M] READ_CLEANUP_ENTER' in b and '[NSC:R204M] READ_CLEANUP_EXIT' in b,
 'deep_read_ready_flag':'deep_read_trace=1' in b and 'READ_STAGE' in b and 'REQUEST_FINALIZE' in b and 'READ_CLEANUP' in b,
 'registry_process_offset':'kLoadOwnerRegistryProcessOffset = 0x1161C98' in b,
 'owner_register_offset':'kLoadOwnerRegisterOffset   = 0x1161B88' in b,
 'registry_process_installed':'LoadOwnerRegistryProcessHook::InstallAtOffset(kLoadOwnerRegistryProcessOffset);' in b,
 'no_cpk_bind_install':'CpkBindHook::Install' not in b[b.index('bool InstallR204MFullPreviewPipelineTrace()'):b.index('bool InstallPlayActionProbe()')],
 'no_path_rewrite':'path_rewrite=0' in b and 'return_override=0' in b,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)

def decode_text(path):
    raw=path.read_bytes()
    if raw[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',raw,o)[0]
    flags=u(0x0c); fo,sz,csz=u(0x10),u(0x18),u(0x60)
    blob=raw[fo:fo+(csz if flags&1 else sz)]
    if flags&1:
        if lz4 is None: raise RuntimeError('lz4 required')
        blob=lz4.block.decompress(blob,uncompressed_size=sz)
    return blob
text=decode_text(r/'original/atmosphere/contents/0100FA10190A0000/exefs/main')
def words(off,n=8): return [struct.unpack_from('<I',text,off+4*i)[0] for i in range(n)]
checks2={
 'main_owner_register_fingerprint':words(0x1161B88)==[0xD10143FF,0xA90167FE,0xA9025FF8,0xA90357F6,0xA9044FF4,0xF9400008,0x2A0403F5,0x2A0303F6],
 'main_registry_process_fingerprint':words(0x1161C98)==[0xF81E0FFE,0xA9014FF4,0xF9400C14,0x91008013,0x14000002,0xAA0903F4,0xEB13029F,0x540002E0],
 'main_owner_ready_fingerprint':words(0x11617CC)==[0xA9BE57FE,0xA9014FF4,0xF9401C08,0xB40000E8,0xAA0003F5,0x38408EA8,0xAA0003F3,0x37000108],
 'main_read_dispatch_fingerprint':words(0x11705F0)==[0xF9001001,0xF9400028,0xF9402502,0xAA0103E0,0xD61F0040,0xF81E0FFE,0xA9014FF4,0x2A0103F4],
 'main_read_stage_fingerprint':words(0x120A860)==[0xA9BD5FFE,0xA90157F6,0xA9024FF4,0xAA0103F6,0xF940E401,0xAA0003F3,0xD0004200,0x912E9C00],
 'main_request_finalize_fingerprint':words(0x1171080)==[0xF81F0FFE,0x6F00E400,0xAA0003E8,0x90007ECA,0x3C838D00,0x12800009,0xAD008100,0x3D803D00],
 'main_read_cleanup_fingerprint':words(0x1170550)==[0xF81E0FFE,0xA9014FF4,0xAA0003F4,0xAA0003F3,0xF8420E80,0xB40001A0,0xF9400008,0xB9400A61],
}
for k,v in checks2.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks2.values()): sys.exit(1)
print('R204M_SOURCE_VERIFY=PASS')
