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
 'core_calls_r204k_only':'return nsc::InstallR204KNativeCharselChildTrace();' in c,
 'no_gameplay_installer_in_core':all(x not in c for x in ['InstallP128','InstallR172','InstallR175','InstallR176','InstallR177','InstallV2N','InstallV2P','InstallResolverHookMigrationProbe','InstallOriginalMainRuntimePatches']),
 'public_decl':'bool InstallR204KNativeCharselChildTrace();' in h,
 'ready_marker':'[NSC:R204K] READY' in b and 'registry_process_trace=1' in b and 'tree_verify=1' in b,
 'owner_tree_verify':'[NSC:R204K] OWNER_TREE_VERIFY' in b and 'same_owner=%u' in b,
 'registry_process':'[NSC:R204K] REGISTRY_PROCESS' in b,
 'target_scan':'[NSC:R204K] TARGET_REGISTRY_OWNER_READY' in b,
 'generic_bod1_path_trace':'data/spc/bod1' in b,
 'generic_bod1_key_trace':'BoundedContains(key, "bod1", 256, 4)' in b,
 'generic_bod1_ready_flag':'generic_bod1_trace=1' in b,
 'registry_process_offset':'kLoadOwnerRegistryProcessOffset = 0x1161C98' in b,
 'owner_register_offset':'kLoadOwnerRegisterOffset   = 0x1161B88' in b,
 'registry_process_installed':'LoadOwnerRegistryProcessHook::InstallAtOffset(kLoadOwnerRegistryProcessOffset);' in b,
 'no_cpk_bind_install':'CpkBindHook::Install' not in b[b.index('bool InstallR204KNativeCharselChildTrace()'):b.index('bool InstallPlayActionProbe()')],
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
}
for k,v in checks2.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks2.values()): sys.exit(1)
print('R204K_SOURCE_VERIFY=PASS')
