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
 'core_calls_r248_only':'return nsc::InstallR248CreateIdentityReadinessTrace();' in CORE,
 'public_decl':'bool InstallR248CreateIdentityReadinessTrace();' in HPP,
 'ready_marker':'[NSC:R248] READY' in CPP and 'hooks=6' in CPP,
 'identity_marker':'[NSC:R248] IDENTITY_LOOKUP' in CPP,
 'descriptor_marker':'[NSC:R248] DESCRIPTOR_LOOKUP' in CPP,
 'ready_pred_marker':'[NSC:R248] READY_PREDICATE' in CPP,
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'six_installs':sum(CPP.count(x+'::InstallAtOffset') for x in [
    'R248TargetRegistryCaptureHook','R248CreateEnterHook','R248DescriptorLookupHook',
    'R248ModelInitHook','R248IdentityLookupHook','R248ReadyPredicateHook']) == 6,
 'offset_descriptor':'kR248DescriptorLookupOffset = 0x64ED30' in CPP,
 'offset_model_init':'kR248ModelInitOffset        = 0x6EAC24' in CPP,
 'offset_identity':'kR248IdentityLookupOffset   = 0x3F4130' in CPP,
 'offset_ready':'kR248ReadyPredicateOffset   = 0x6ECBB0' in CPP,
 'workflow_verify':'python3 verify_r248.py' in WF,
 'workflow_artifact':'NSC2Switch-R248-CREATE-IDENTITY-READINESS-TRACE' in WF,
 'workflow_no_main':'test ! -e out/runtime/atmosphere/contents/0100FA10190A0000/exefs/main' in WF,
 'no_gameplay_core':all(x not in CORE for x in ['InstallP128','InstallR172','InstallV2P','InstallOriginalMainRuntimePatches']),
}
for k,v in checks.items():
    print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()):
    sys.exit(1)

raw=MAIN.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
print('original_main_sha256='+sha)
if sha != EXPECTED_MAIN_SHA:
    print('original_main_sha256_match=FAIL'); sys.exit(1)
print('original_main_sha256_match=PASS')

def decode_text(raw):
    if raw[:4] != b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o: struct.unpack_from('<I',raw,o)[0]
    flags,fo,sz,csz=u(0x0c),u(0x10),u(0x18),u(0x60)
    blob=raw[fo:fo+(csz if flags & 1 else sz)]
    if flags & 1:
        if lz4 is None: raise RuntimeError('lz4 required')
        blob=lz4.block.decompress(blob,uncompressed_size=sz)
    return blob

text=decode_text(raw)
def words(off,n):
    return list(struct.unpack_from('<'+'I'*n,text,off))

expected={
 'owner_register_fingerprint':(0x1161B88,[0xD10143FF,0xA90167FE,0xA9025FF8,0xA90357F6,0xA9044FF4,0xF9400008,0x2A0403F5,0x2A0303F6]),
 'create_enter_fingerprint':(0x549868,[0xF81E0FFE,0xA9014FF4,0xF9400008,0xAA0003F3,0xF9400908,0xD63F0100,0xF9405A68,0xB40000E8]),
 'create_enter_descriptor_flow':(0x5498D0,[0xF9409900,0xB940CE61,0x94041516,0xB4FFFD60,0xF9405A68,0x29408801,0x29431003,0xAA0803E0,0xB9414665,0xB9410E66,0x94068479]),
 'create_update_fingerprint':(0x54991C,[0xA9BF4FFE,0xAA0003F3,0xF9405800,0xB40000E0,0x94068CA1,0x340000A0,0x52800028,0xB9006E68,0xB940D268,0xB9005E68]),
 'descriptor_lookup_fingerprint':(0x64ED30,[0xF8408409,0x14000002,0xAA0A03E9,0xEB00013F,0x540002E0,0xAA0903E8,0xB8428D0A,0x6B01015F]),
 'model_init_fingerprint':(0x6EAC24,[0xD10283FF,0xFD003BE8,0xA90857FE,0xA9094FF4,0xF9400008,0xAA0003F3,0xF9400908,0xD63F0100]),
 'model_init_identity_gate':(0x6EAC44,[0xAA1303E0,0x97FFFEDA,0xB9403A60,0x97F42538,0xB4001E20]),
 'model_ready90_store':(0x6EAD90,[0xB9404261,0xAA1303E0,0xF9004A75,0x9400015A,0xF9404A68]),
 'identity_lookup_fingerprint':(0x3F4130,[0xF000EA68,0xF9424508,0xF9760908,0x2A0003E1,0xF9409500,0x1410AC8E]),
 'ready_predicate_fingerprint':(0x6ECBB0,[0xF9404808,0xF100011F,0x1A9F07E0,0xD65F03C0]),
}
for name,(off,exp) in expected.items():
    ok=words(off,len(exp))==exp
    print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok:
        print(' got='+','.join(f'0x{x:08X}' for x in words(off,len(exp))))
        print(' exp='+','.join(f'0x{x:08X}' for x in exp))
        sys.exit(1)

# Decode exact direct BL target from Create::update.
ins=words(0x54992C,1)[0]
imm=ins & 0x03ffffff
if imm & (1<<25): imm -= 1<<26
target=0x54992C + (imm<<2)
print(f'create_update_bl_target=0x{target:X}')
if target != 0x6ECBB0:
    print('create_update_bl_target_match=FAIL'); sys.exit(1)
print('create_update_bl_target_match=PASS')

# Decode null branch after identity lookup in model init.
ins=words(0x6EAC54,1)[0]
imm19=(ins>>5)&0x7ffff
if imm19 & (1<<18): imm19 -= 1<<19
target=0x6EAC54 + (imm19<<2)
print(f'model_init_identity_null_branch=0x{target:X}')
if target != 0x6EB018:
    print('model_init_identity_null_branch_match=FAIL'); sys.exit(1)
print('model_init_identity_null_branch_match=PASS')

print('R248_SOURCE_VERIFY=PASS')
