#!/usr/bin/env python3
from pathlib import Path
import struct, sys
try:
    import lz4.block
except Exception:
    lz4 = None
root=Path(__file__).resolve().parent
core=(root/'overlay/source/program/nsc_runtime_core.cpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
checks={
 'core_calls_r204d_only': 'return nsc::InstallR204DNativeMtobProcessTrace();' in core,
 'no_gameplay_installer_in_core': all(x not in core for x in ['InstallP128','InstallR172','InstallR175','InstallR176','InstallR177','InstallV2N','InstallV2P','InstallResolverHookMigrationProbe','InstallOriginalMainRuntimePatches']),
 'public_decl': 'bool InstallR204DNativeMtobProcessTrace();' in hpp,
 'ready_marker': '[NSC:R204D] READY' in bridge and 'completion_writers=1' in bridge,
 'load_req': '[NSC:R204D] LOAD_REQ' in bridge,
 'load_create': '[NSC:R204D] LOAD_CREATE' in bridge,
 'load_status': '[NSC:R204D] LOAD_STATUS' in bridge,
 'file_open': '[NSC:R204D] FILE_OPEN' in bridge,
 'process': '[NSC:R204D] PROCESS' in bridge,
 'chunk': '[NSC:R204D] CHUNK' in bridge,
 'state_set': '[NSC:R204D] STATE_SET' in bridge,
 'success_set': '[NSC:R204D] SUCCESS_SET' in bridge,
 'process_offset': 'kLoadRequestProcessOffset = 0x116F404' in bridge,
 'state_set_offset': 'kLoadStateSetOffset       = 0x120661C' in bridge,
 'success_set_offset': 'kLoadSuccessSetOffset     = 0x1206690' in bridge,
 'load_pointer_tracking': all(x in bridge for x in ['TrackLoadPath(result, path)','LookupLoadPath(load_object, path, sizeof(path))','LoadPathEntry g_load_path_entries[128]']),
 'state_set_installed': 'LoadStateSetHook::InstallAtOffset(kLoadStateSetOffset);' in bridge,
 'success_set_installed': 'LoadSuccessSetHook::InstallAtOffset(kLoadSuccessSetOffset);' in bridge,
 'no_cpk_bind_install': 'CpkBindHook::Install' not in bridge[bridge.index('bool InstallR204DNativeMtobProcessTrace()'):bridge.index('bool InstallPlayActionProbe()')],
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)

def decode_text(path):
    b=path.read_bytes()
    if b[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',b,o)[0]
    flags=u(0x0c); fo,sz,csz=u(0x10),u(0x18),u(0x60)
    blob=b[fo:fo+(csz if flags&1 else sz)]
    if flags&1:
        if lz4 is None: raise RuntimeError('lz4 required')
        blob=lz4.block.decompress(blob,uncompressed_size=sz)
    return blob
text=decode_text(root/'original/atmosphere/contents/0100FA10190A0000/exefs/main')
def words(off,n): return [struct.unpack_from('<I',text,off+4*i)[0] for i in range(n)]
expected_state=[0xA9BE57FE,0xA9014FF4,0x91006013,0xAA0003F5,0xAA1303E0,0x2A0103F4,0x94003B49,0xB9406AA8]
expected_success=[0xA9BE57FE,0xA9014FF4,0x91006015,0xAA0003F4,0xAA1503E0,0xAA0103F3,0x94003B2C,0x52800048]
print('main_state_set_fingerprint=' + ('PASS' if words(0x120661C,8)==expected_state else 'FAIL'))
print('main_success_set_fingerprint=' + ('PASS' if words(0x1206690,8)==expected_success else 'FAIL'))
if words(0x120661C,8)!=expected_state or words(0x1206690,8)!=expected_success: sys.exit(1)
# Prove unique direct BL caller of success setter.
target=0x1206690
callers=[]
for off in range(0,len(text)-3,4):
    w=struct.unpack_from('<I',text,off)[0]
    if (w>>26)==0b100101:
        imm=w&0x03ffffff
        if imm&(1<<25): imm-=1<<26
        if off+(imm<<2)==target: callers.append(off)
print('success_set_direct_callers=' + ','.join(hex(x) for x in callers))
print('success_set_unique_caller=' + ('PASS' if callers==[0x116F370] else 'FAIL'))
if callers != [0x116F370]: sys.exit(1)
print('R204D_SOURCE_VERIFY=PASS')
