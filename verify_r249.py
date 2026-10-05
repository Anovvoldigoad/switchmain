#!/usr/bin/env python3
from pathlib import Path
import hashlib, struct, sys
try:
    import lz4.block
except Exception:
    lz4 = None
ROOT=Path(__file__).resolve().parent
CPP=(ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
HPP=(ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
CORE=(ROOT/'overlay/source/program/nsc_runtime_core.cpp').read_text()
WF=(ROOT/'.github/workflows/build-runtime-r181.yml').read_text()
MAIN=ROOT/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
EXPECTED_MAIN_SHA='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
checks={
 'core_calls_r249_only':'return nsc::InstallR249PostLookupResourceTrace();' in CORE,
 'public_decl':'bool InstallR249PostLookupResourceTrace();' in HPP,
 'ready_marker':'[NSC:R249] READY' in CPP and 'hooks=6' in CPP,
 'resource_marker':'[NSC:R249] RESOURCE_GATE' in CPP,
 'chunk_marker':'[NSC:R249] CHUNK_GATE' in CPP,
 'alloc_marker':'[NSC:R249] ALLOC' in CPP,
 'model_marker':'[NSC:R249] MODEL_INIT' in CPP,
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'six_installs':sum(CPP.count(x+'::InstallAtOffset') for x in [
     'R248TargetRegistryCaptureHook','R248CreateEnterHook','R249ModelInitScopeHook',
     'R249FileResourceLookupHook','R249ChunkResourceLookupHook','R249AllocatorHook']) >= 6,
 'offset_allocator':'kR249AllocatorOffset        = 0x116AE60' in CPP,
 'workflow_verify':'python3 verify_r249.py' in WF,
 'workflow_artifact':'NSC2Switch-R249-POST-IDENTITY-RESOURCE-TRACE' in WF,
 'workflow_no_main':'test ! -e out/runtime/atmosphere/contents/0100FA10190A0000/exefs/main' in WF,
 'no_gameplay_core':all(x not in CORE for x in ['InstallP128','InstallR172','InstallV2P','InstallOriginalMainRuntimePatches']),
}
for k,v in checks.items():
    print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
raw=MAIN.read_bytes(); sha=hashlib.sha256(raw).hexdigest(); print('original_main_sha256='+sha)
if sha!=EXPECTED_MAIN_SHA: print('original_main_sha256_match=FAIL'); sys.exit(1)
print('original_main_sha256_match=PASS')
def decode_text(raw):
    if raw[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',raw,o)[0]
    flags,fo,sz,csz=u(0x0c),u(0x10),u(0x18),u(0x60)
    blob=raw[fo:fo+(csz if flags&1 else sz)]
    if flags&1:
        if lz4 is None: raise RuntimeError('lz4 required')
        blob=lz4.block.decompress(blob,uncompressed_size=sz)
    return blob
text=decode_text(raw)
def words(off,n): return list(struct.unpack_from('<'+'I'*n,text,off))
expected={
 'owner_register_fingerprint':(0x1161B88,[0xD10143FF,0xA90167FE,0xA9025FF8,0xA90357F6,0xA9044FF4,0xF9400008,0x2A0403F5,0x2A0303F6]),
 'create_enter_fingerprint':(0x549868,[0xF81E0FFE,0xA9014FF4,0xF9400008,0xAA0003F3,0xF9400908,0xD63F0100,0xF9405A68,0xB40000E8]),
 'model_init_fingerprint':(0x6EAC24,[0xD10283FF,0xFD003BE8,0xA90857FE,0xA9094FF4,0xF9400008,0xAA0003F3,0xF9400908,0xD63F0100]),
 'resource_lookup_fingerprint':(0x1207B38,[0xF81F0FFE,0x97FFFC27,0xB4000060,0xF84107FE,0x17FFFACB,0xF84107FE,0xD65F03C0,0xA9BD5FFE]),
 'chunk_lookup_fingerprint':(0x120A3D4,[0xD10143FF,0xA90357FE,0xA9044FF4,0xAA0203F3,0xAA0103F4,0xB90003FF,0xAA0003F5,0x390013FF]),
 'allocator_fingerprint':(0x116AE60,[0xF81D0FFE,0xA90157F6,0xA9024FF4,0x2A0203F3,0xAA0103F4,0xAA0003F5,0x9400024E,0xAA0003F6]),
 'resource_call_corridor':(0x6EACF0,[0xF942F000,0x9A890281,0x942C7390,0xB4000580]),
 'chunk_call_corridor':(0x6EAD48,[0x910003E2,0xAA1403E0,0x942C7DA1,0xB40002C0]),
 'allocator_call_corridor':(0x6EAD60,[0x9106E421,0x52807600,0x52801842,0x942A003D,0xAA0003F5,0xB40000E0]),
}
for name,(off,exp) in expected.items():
    got=words(off,len(exp)); ok=got==exp; print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok:
        print(' got='+','.join(f'0x{x:08X}' for x in got)); print(' exp='+','.join(f'0x{x:08X}' for x in exp)); sys.exit(1)
def bl_target(off):
    ins=words(off,1)[0]
    if ins & 0xFC000000 != 0x94000000: raise RuntimeError(f'not BL at {off:X}')
    imm=ins&0x03ffffff
    if imm&(1<<25): imm-=1<<26
    return off+(imm<<2)
def cb_target(off):
    ins=words(off,1)[0]; imm=(ins>>5)&0x7ffff
    if imm&(1<<18): imm-=1<<19
    return off+(imm<<2)
for name,off,exp in [
 ('resource_bl_target',0x6EACF8,0x1207B38),('chunk_bl_target',0x6EAD50,0x120A3D4),('allocator_bl_target',0x6EAD6C,0x116AE60)]:
    got=bl_target(off); print(f'{name}=0x{got:X}');
    if got!=exp: print(name+'_match=FAIL'); sys.exit(1)
    print(name+'_match=PASS')
for name,off,exp in [('resource_null_branch',0x6EACFC,0x6EADAC),('chunk_null_branch',0x6EAD54,0x6EADAC)]:
    got=cb_target(off); print(f'{name}=0x{got:X}')
    if got!=exp: print(name+'_match=FAIL'); sys.exit(1)
    print(name+'_match=PASS')
print('R249_SOURCE_VERIFY=PASS')
