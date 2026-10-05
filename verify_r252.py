#!/usr/bin/env python3
from pathlib import Path
import hashlib, struct, sys
try:
    import lz4.block
except Exception:
    lz4=None
ROOT=Path(__file__).resolve().parent
CPP=(ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
HPP=(ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
CORE=(ROOT/'overlay/source/program/nsc_runtime_core.cpp').read_text()
WF=(ROOT/'.github/workflows/build-runtime-r181.yml').read_text()
MAIN=ROOT/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
EXPECTED='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
checks={
 'core_calls_r252_only':'return nsc::InstallR252WaitChildReadinessTrace();' in CORE,
 'public_decl':'bool InstallR252WaitChildReadinessTrace();' in HPP,
 'ready_marker':'[NSC:R252] READY' in CPP,
 'summary_marker':'[NSC:R252] WAIT_SUMMARY' in CPP,
 'child_marker':'[NSC:R252] WAIT_CHILD' in CPP,
 'ready_marker2':'[NSC:R252] WAIT_READY_GATE' in CPP,
 'secondary_marker':'[NSC:R252] WAIT_SECONDARY_GATE' in CPP,
 'consume_marker':'[NSC:R252] WAIT_CONSUME' in CPP,
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'six_installs':sum(CPP.count(x+'::InstallAtOffset') for x in [
   'R252TargetRegistryCaptureHook','R252WaitEnterHook','R252WaitUpdateHook','R252WaitReadyHook','R252WaitSecondaryHook','R252WaitConsumeHook'])==6,
 'offset_wait_enter':'kR252WaitEnterOffset      = 0x549950' in CPP,
 'offset_wait_update':'kR252WaitUpdateOffset     = 0x549B80' in CPP,
 'offset_ready':'kR252WaitReadyOffset      = 0x58498' in CPP,
 'offset_secondary':'kR252WaitSecondaryOffset  = 0x58490' in CPP,
 'offset_consume':'kR252WaitConsumeOffset    = 0x54ADE8' in CPP,
 'workflow_verify':'python3 verify_r252.py' in WF,
 'workflow_artifact':'NSC2Switch-R252-WAIT-CHILD-READINESS-TRACE' in WF,
 'workflow_no_main':'test ! -e out/runtime/atmosphere/contents/0100FA10190A0000/exefs/main' in WF,
 'no_gameplay_core':all(x not in CORE for x in ['InstallP128','InstallR172','InstallV2P','InstallOriginalMainRuntimePatches']),
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
raw=MAIN.read_bytes(); sha=hashlib.sha256(raw).hexdigest(); print('original_main_sha256='+sha)
if sha!=EXPECTED: print('original_main_sha256_match=FAIL'); sys.exit(1)
print('original_main_sha256_match=PASS')
def decode(raw):
    if raw[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',raw,o)[0]
    flags,fo,sz,csz=u(0x0c),u(0x10),u(0x18),u(0x60)
    blob=raw[fo:fo+(csz if flags&1 else sz)]
    if flags&1:
        if lz4 is None: raise RuntimeError('lz4 required')
        blob=lz4.block.decompress(blob,uncompressed_size=sz)
    return blob
text=decode(raw)
def words(off,n): return list(struct.unpack_from('<'+'I'*n,text,off))
expected={
 'owner_register_fingerprint':(0x1161B88,[0xD10143FF,0xA90167FE,0xA9025FF8,0xA90357F6,0xA9044FF4,0xF9400008,0x2A0403F5,0x2A0303F6]),
 'wait_enter_fingerprint':(0x549950,[0xD10303FF,0xA9095FFE,0xA90A57F6,0xA90B4FF4,0xF9405808,0xB4001048,0xD000DFD6,0xF94246D6]),
 'wait_update_fingerprint':(0x549B80,[0x14000001,0xF81D0FFE,0xA90157F6,0xA9024FF4,0xB9414008,0x340004C8,0xA958A015,0xAA0003F3]),
 'wait_ready_fingerprint':(0x58498,[0x91002000,0x14442621]),
 'wait_secondary_fingerprint':(0x58490,[0x91002000,0x14442601]),
 'wait_consume_fingerprint':(0x54ADE8,[0xD10303FF,0xA9076FFE,0xA90867FA,0xA9095FF8,0xA90A57F6,0xA90B4FF4,0xF9405808,0xB4001CE8]),
}
for name,(off,exp) in expected.items():
    ok=words(off,len(exp))==exp
    print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok: sys.exit(1)
# exact Wait-update call targets / control-flow fingerprints
w=words(0x549BE4,18)
# 0x549BF0 BL -> 0x58498, 0x549BFC BL -> 0x58490, 0x549BC8 BL -> 0x54ADE8 checked separately.
def bl_target(pc,insn):
    imm=insn & 0x03ffffff
    if imm & 0x02000000: imm-=0x04000000
    return pc + (imm<<2)
checks2={
 'wait_ready_call_target':bl_target(0x549BF0,words(0x549BF0,1)[0])==0x58498,
 'wait_secondary_call_target':bl_target(0x549BFC,words(0x549BFC,1)[0])==0x58490,
 'wait_consume_call_target':bl_target(0x549BC8,words(0x549BC8,1)[0])==0x54ADE8,
 'wait_ready_zero_skips_child':words(0x549BF4,1)[0]==0x34FFFF00,
 'wait_child_ready_store':words(0x549BCC,2)==[0xF94002A8,0xB900E516],
}
for k,v in checks2.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks2.values()): sys.exit(1)
print('R252_SOURCE_VERIFY=PASS')
