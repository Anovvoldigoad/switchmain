#!/usr/bin/env python3
from pathlib import Path
import struct, sys
try:
    import lz4.block
except Exception:
    lz4=None
root=Path(__file__).resolve().parent
core=(root/"overlay/source/program/nsc_runtime_core.cpp").read_text()
bridge=(root/"overlay/source/program/nsc_cpk_bridge.cpp").read_text()
hpp=(root/"overlay/source/program/nsc_cpk_bridge.hpp").read_text()
checks={
 "core_calls_r204i_only":"return nsc::InstallR204INativeCharselOwnerTrace();" in core,
 "no_gameplay_installer_in_core":all(x not in core for x in ["InstallP128","InstallR172","InstallR175","InstallR176","InstallR177","InstallV2N","InstallV2P","InstallResolverHookMigrationProbe","InstallOriginalMainRuntimePatches"]),
 "public_decl":"bool InstallR204INativeCharselOwnerTrace();" in hpp,
 "ready_marker":"[NSC:R204I] READY" in bridge and "resource_consumers=1" in bridge,
 "success_set":"[NSC:R204I] SUCCESS_SET" in bridge,
 "resource_lookup":"[NSC:R204I] RESOURCE_LOOKUP" in bridge,
 "chunk_low":"[NSC:R204I] CHUNK_LOW" in bridge,
 "chunk_key_text":all(x in bridge for x in ["key_text[97]", "key_printable=%u", "key_len=%u", "key_text=%s"]),
 "trace_1nrt_path":'BoundedContains(path, "1nrt", 512, 8)' in bridge,
 "trace_1nrt_key":'BoundedContains(key, "1nrt", 256, 8)' in bridge,
 "trace_all_charsel":'BoundedContains(path, "charsel.xfbin", 512, 13)' in bridge,
 "owner_init":"[NSC:R204I] OWNER_INIT" in bridge,
 "owner_init5":"[NSC:R204I] OWNER_INIT5" in bridge,
 "owner_register":"[NSC:R204I] OWNER_REGISTER" in bridge,
 "owner_ready":"[NSC:R204I] OWNER_READY" in bridge,
 "owner_state":"[NSC:R204I] OWNER_STATE" in bridge,
 "owner_init_offset":"kLoadOwnerInitOffset       = 0x11616E8" in bridge,
 "owner_init5_offset":"kLoadOwnerInitWideOffset   = 0x116175C" in bridge,
 "owner_register_offset":"kLoadOwnerRegisterOffset   = 0x1161B88" in bridge,
 "owner_ready_offset":"kLoadOwnerReadyOffset      = 0x11617CC" in bridge,
 "owner_state_offset":"kLoadOwnerStateOffset      = 0x1161858" in bridge,
 "owner_init_installed":"LoadOwnerInitHook::InstallAtOffset(kLoadOwnerInitOffset);" in bridge,
 "owner_ready_installed":"LoadOwnerReadyHook::InstallAtOffset(kLoadOwnerReadyOffset);" in bridge,
 "owner_state_installed":"LoadOwnerStateHook::InstallAtOffset(kLoadOwnerStateOffset);" in bridge,
 "resource_lookup_offset":"kFileResourceLookupOffset = 0x1207B38" in bridge,
 "chunk_low_offset":"kChunkResourceLookupOffset = 0x120A3D4" in bridge,
 "resource_tracking":all(x in bridge for x in ["TrackResourcePath(resource, path)","LookupResourcePath(resource, path, sizeof(path))","ResourcePathEntry g_resource_path_entries[128]"]),
 "resource_lookup_installed":"FileResourceLookupHook::InstallAtOffset(kFileResourceLookupOffset);" in bridge,
 "chunk_low_installed":"ChunkResourceLookupHook::InstallAtOffset(kChunkResourceLookupOffset);" in bridge,
 "no_cpk_bind_install":"CpkBindHook::Install" not in bridge[bridge.index("bool InstallR204INativeCharselOwnerTrace()"):bridge.index("bool InstallPlayActionProbe()")],
}
for k,v in checks.items(): print(f"{k}={'PASS' if v else 'FAIL'}")
if not all(checks.values()): sys.exit(1)

def decode_text(path):
    b=path.read_bytes()
    if b[:4]!=b"NSO0": raise RuntimeError("not NSO0")
    u=lambda o:struct.unpack_from("<I",b,o)[0]
    flags=u(0x0c); fo,sz,csz=u(0x10),u(0x18),u(0x60)
    blob=b[fo:fo+(csz if flags&1 else sz)]
    if flags&1:
        if lz4 is None: raise RuntimeError("lz4 required")
        blob=lz4.block.decompress(blob,uncompressed_size=sz)
    return blob
text=decode_text(root/"original/atmosphere/contents/0100FA10190A0000/exefs/main")
def words(off,n): return [struct.unpack_from("<I",text,off+4*i)[0] for i in range(n)]
expected_lookup=[0xF81F0FFE,0x97FFFC27,0xB4000060,0xF84107FE,0x17FFFACB,0xF84107FE,0xD65F03C0,0xA9BD5FFE]
expected_chunk=[0xD10143FF,0xA90357FE,0xA9044FF4,0xAA0203F3,0xAA0103F4,0xB90003FF,0xAA0003F5,0x390013FF]
expected_owner_init=[0xD10103FF,0xA90257FE,0xA9034FF4,0x2F07E600,0xAA0003F4,0xF90007FF,0xB90013E2,0xD0007F00]
expected_owner_init5=[0xD10103FF,0xA90257FE,0xA9034FF4,0xAA0003F4,0xF90007FF,0xD0007F00,0x29020FE2,0x910023E2]
expected_owner_register=[0xD10143FF,0xA90167FE,0xA9025FF8,0xA90357F6,0xA9044FF4,0xF9400008,0x2A0403F5,0x2A0303F6]
expected_owner_ready=[0xA9BE57FE,0xA9014FF4,0xF9401C08,0xB40000E8,0xAA0003F5,0x38408EA8,0xAA0003F3,0x37000108]
expected_owner_state=[0xF81F0FFE,0xF9401C08,0xB4000248,0xAA0003E8,0x38408D09,0x37000069,0x91000501,0x14000002]
checks2={
 "main_resource_lookup_fingerprint":words(0x1207B38,8)==expected_lookup,
 "main_chunk_low_fingerprint":words(0x120A3D4,8)==expected_chunk,
 "main_owner_init_fingerprint":words(0x11616E8,8)==expected_owner_init,
 "main_owner_init5_fingerprint":words(0x116175C,8)==expected_owner_init5,
 "main_owner_register_fingerprint":words(0x1161B88,8)==expected_owner_register,
 "main_owner_ready_fingerprint":words(0x11617CC,8)==expected_owner_ready,
 "main_owner_state_fingerprint":words(0x1161858,8)==expected_owner_state,
}
for k,v in checks2.items(): print(f"{k}={'PASS' if v else 'FAIL'}")
if not all(checks2.values()): sys.exit(1)
print("R204I_SOURCE_VERIFY=PASS")
