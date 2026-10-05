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
 'core_calls_r253_only':'return nsc::InstallR253LoadChildConstructionTrace();' in CORE,
 'public_decl':'bool InstallR253LoadChildConstructionTrace();' in HPP,
 'ready_marker':'[NSC:R253] READY' in CPP,
 'load_vector_marker':'[NSC:R253] LOAD_VECTOR' in CPP,
 'source_marker':'[NSC:R253] SOURCE_LIST' in CPP,
 'candidate_marker':'[NSC:R253] CANDIDATE_RESOLVE' in CPP,
 'producer_marker':'[NSC:R253] CHILD_PRODUCER' in CPP,
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'five_installs':sum(CPP.count(x+'::InstallAtOffset') for x in [
   'R253TargetRegistryCaptureHook','R253LoadEnterHook','R253SourceListBuildHook','R253CandidateResolveHook','R253ChildProducerHook'])==5,
 'offset_load':'kR253LoadEnterOffset          = 0x548094' in CPP,
 'offset_source':'kR253SourceListBuildOffset    = 0x3FCE60' in CPP,
 'offset_candidate':'kR253CandidateResolveOffset   = 0x3FBC4C' in CPP,
 'offset_producer':'kR253ChildProducerOffset      = 0x549610' in CPP,
 'workflow_verify':'python3 verify_r253.py' in WF,
 'workflow_artifact':'NSC2Switch-R253-LOAD-CHILD-CONSTRUCTION-TRACE' in WF,
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
def bl_target(pc,insn):
    if (insn & 0xFC000000) != 0x94000000: return None
    imm=insn & 0x03ffffff
    if imm & 0x02000000: imm-=0x04000000
    return pc + (imm<<2)
expected={
 'owner_register_fingerprint':(0x1161B88,[0xD10143FF,0xA90167FE,0xA9025FF8,0xA90357F6,0xA9044FF4,0xF9400008,0x2A0403F5,0x2A0303F6]),
 'load_enter_fingerprint':(0x548094,[0xD10643FF,0xA9137BFD,0xA9146FFC,0xA91567FA,0xA9165FF8,0xA91757F6,0xA9184FF4,0xF9400008]),
 'source_list_fingerprint':(0x3FCE60,[0xF81D0FFE,0xA90157F6,0xA9024FF4,0xF9400028,0xF9000428,0xA941A016,0xEB0802DF,0x54000220]),
 'candidate_fingerprint':(0x3FBC4C,[0xF9402400,0xD65F03C0,0x91014000,0xD65F03C0,0x91017000,0xD65F03C0,0xA9BF4FFE,0xF9400800]),
 'producer_fingerprint':(0x549610,[0xD101C3FF,0xA90367FE,0xA9045FF8,0xA90557F6,0xA9064FF4,0xD000DFC8,0xF9424508,0xF976B509]),
}
for name,(off,exp) in expected.items():
    ok=words(off,len(exp))==exp
    print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok: sys.exit(1)
callers=[0x548F4C,0x548FE0,0x549078,0x549110,0x54924C,0x54BC18]
for pc in callers:
    ok=bl_target(pc,words(pc,1)[0])==0x549610
    print(f'producer_call_{pc:06X}={"PASS" if ok else "FAIL"}')
    if not ok: sys.exit(1)
checks2={
 'source_builder_call_target':bl_target(0x548DE4,words(0x548DE4,1)[0])==0x3FCE60,
 'vector_fast_append_end_store':words(0x5496FC,5)==[0xA9592269,0xEB08013F,0x54000080,0xF8008534,0xF900CA69],
 'vector_growth_store_pair':words(0x5497C0,2)==[0xA918AA69,0xF900CE68],
 'producer_descriptor_lookup':bl_target(0x54964C,words(0x54964C,1)[0])==0x64ED30,
 'producer_descriptor_null_exit':words(0x549650,1)[0]==0xB4000CA0,
}
for k,v in checks2.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks2.values()): sys.exit(1)
print('R253_SOURCE_VERIFY=PASS')
