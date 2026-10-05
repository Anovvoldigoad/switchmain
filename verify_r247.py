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
 'core_calls_r247_only':'return nsc::InstallR247R204WStateTableRetest();' in CORE,
 'public_decl':'bool InstallR247R204WStateTableRetest();' in HPP,
 'ready_marker':'[NSC:R247] READY' in CPP and 'reconstructed_r204w=1' in CPP,
 'capture_marker':'[NSC:R247] TARGET_REGISTRY_CAPTURE' in CPP,
 'state_marker':'[NSC:R247] STATE_CALL' in CPP,
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'nine_installs':sum(CPP.count(x+'::InstallAtOffset') for x in [
    'R247TargetRegistryCaptureHook','R247LoadEnterHook','R247LoadUpdateHook','R247CreateEnterHook',
    'R247CreateUpdateHook','R247WaitEnterHook','R247WaitUpdateHook','R247SelectEnterHook','R247SelectUpdateHook']) == 9,
 'offset_load_enter':'kR247LoadEnterOffset   = 0x548094' in CPP,
 'offset_load_update':'kR247LoadUpdateOffset  = 0x549804' in CPP,
 'offset_create_enter':'kR247CreateEnterOffset = 0x549868' in CPP,
 'offset_create_update':'kR247CreateUpdateOffset= 0x54991C' in CPP,
 'offset_wait_enter':'kR247WaitEnterOffset   = 0x549950' in CPP,
 'offset_wait_update':'kR247WaitUpdateOffset  = 0x549B80' in CPP,
 'offset_select_enter':'kR247SelectEnterOffset = 0x549C40' in CPP,
 'offset_select_update':'kR247SelectUpdateOffset= 0x549EA8' in CPP,
 'workflow_verify':'python3 verify_r247.py' in WF,
 'workflow_artifact':'NSC2Switch-R247-R204W-STATE-TABLE-RETEST' in WF,
 'workflow_no_main':'test ! -e out/runtime/atmosphere/contents/0100FA10190A0000/exefs/main' in WF,
 'no_gameplay_core':all(x not in CORE for x in ['InstallP128','InstallR172','InstallV2P','InstallOriginalMainRuntimePatches']),
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
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
def words(off,n): return list(struct.unpack_from('<'+'I'*n,text,off))
expected={
 'owner_register_fingerprint':(0x1161B88,[0xD10143FF,0xA90167FE,0xA9025FF8,0xA90357F6,0xA9044FF4,0xF9400008,0x2A0403F5,0x2A0303F6]),
 'load_enter_fingerprint':(0x548094,[0xD10643FF,0xA9137BFD,0xA9146FFC,0xA91567FA,0xA9165FF8,0xA91757F6,0xA9184FF4,0xF9400008]),
 'load_update_fingerprint':(0x549804,[0xA9BF4FFE,0xAA0003F3,0xF9405400,0xB4000260,0x94306121,0x34000220,0xF9406260,0xB40000C0]),
 'create_enter_fingerprint':(0x549868,[0xF81E0FFE,0xA9014FF4,0xF9400008,0xAA0003F3,0xF9400908,0xD63F0100,0xF9405A68,0xB40000E8]),
 'create_update_fingerprint':(0x54991C,[0xA9BF4FFE,0xAA0003F3,0xF9405800,0xB40000E0,0x94068CA1,0x340000A0,0x52800028,0xB9006E68]),
 'wait_enter_fingerprint':(0x549950,[0xD10303FF,0xA9095FFE,0xA90A57F6,0xA90B4FF4,0xF9405808,0xB4001048,0xD000DFD6,0xF94246D6]),
 'wait_update_fingerprint':(0x549B80,[0x14000001,0xF81D0FFE,0xA90157F6,0xA9024FF4,0xB9414008,0x340004C8,0xA958A015,0xAA0003F3]),
 'select_enter_fingerprint':(0x549C40,[0xD10303FF,0xA9095FFE,0xA90A57F6,0xA90B4FF4,0xF9405808,0xB4001208,0xD000DFD6,0xF94246D6]),
 'select_update_fingerprint':(0x549EA8,[0xA9BF4FFE,0xAA0003F3,0xF9405800,0xB40000E0,0x94068B46,0x340000A0,0x52800028,0xB9006E68]),
}
for name,(off,exp) in expected.items():
    ok=words(off,len(exp))==exp
    print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok: sys.exit(1)
print('R247_SOURCE_VERIFY=PASS')
