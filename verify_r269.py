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
 'core_calls_r269_only':'return nsc::InstallR269BaseVisualPopulationTrace();' in CORE and 'return nsc::InstallR268BaseVisualChildGateTrace();' not in CORE,
 'public_decl':'bool InstallR269BaseVisualPopulationTrace();' in HPP,
 'ready_marker':'[NSC:R269] READY' in CPP,
 'source_link_markers':'[NSC:R269] SOURCE_LINK_PRE' in CPP and '[NSC:R269] SOURCE_LINK_POST' in CPP,
 'populate_markers':'[NSC:R269] POPULATE_PRE' in CPP and '[NSC:R269] POPULATE_POST' in CPP,
 'match_markers':'[NSC:R269] MATCH_PRE' in CPP and '[NSC:R269] MATCH_POST' in CPP,
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'r269_installs':sum(CPP.count(x+'::InstallAtOffset') for x in ['R269VisualSourceLinkHook','R269VisualPopulateHook','R269VisualCandidateMatchHook'])==3,
 'offset_source_link':'kR269VisualSourceLinkOffset        = 0x117D390' in CPP,
 'offset_populate':'kR269VisualPopulateOffset          = 0x117BA00' in CPP,
 'offset_match':'kR269VisualCandidateMatchOffset    = 0x11A2D4C' in CPP,
 'workflow_verify':'python3 verify_r269.py' in WF,
 'workflow_artifact':'NSC2Switch-R269-BASE-VISUAL-POPULATION-TRACE' in WF,
 'workflow_no_main':'test ! -e out/runtime/atmosphere/contents/0100FA10190A0000/exefs/main' in WF,
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
    return pc+(imm<<2)
expected={
 'base_model_draw_fingerprint':(0x6ECAE4,[0xF81E0FFE,0xA9014FF4,0xAA0003F3,0xF9404C00,0xB4000160,0xB96A9268,0x340000A8,0xF9400C08]),
 'base_visual_list_fingerprint':(0x117E0D8,[0xA9BE57FE,0xA9014FF4,0xF9401408,0xB4000288,0x79404109,0x34000249,0x52800D0A,0x9B0A7D29]),
 'visual_populate_fingerprint':(0x117BA00,[0xD10383FF,0xFD003BE8,0xA9087BFD,0xA9096FFC,0xA90A67FA,0xA90B5FF8,0xA90C57F6,0xA90D4FF4]),
 'candidate_match_fingerprint':(0x11A2D4C,[0xA9BE57FE,0xA9014FF4,0xAA0003F3,0xF9400C00,0xAA0103F4,0xF9400008,0xF9400D08,0xD63F0100]),
 'source_link_fingerprint':(0x117D390,[0xF900C401,0xD65F03C0,0xF940C408,0xB4000068,0x52800020,0xD65F03C0,0xF9401408,0xB4000128]),
}
for name,(off,exp) in expected.items():
    ok=words(off,len(exp))==exp
    print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok: sys.exit(1)
chain={
 'builder_links_base90_before_vcall68': words(0x6EB728,1)[0]==0xF9404A61 and bl_target(0x6EB730,words(0x6EB730,1)[0])==0x117D390 and words(0x6EB740,1)[0]==0xF9403508,
 'source_link_store188': words(0x117D390,1)[0]==0xF900C401,
 'populate_typed_count_b0': words(0x117BAF0,1)[0]==0x794162C8,
 'populate_source188': words(0x117BAFC,1)[0]==0xF940C7B9,
 'populate_list28': words(0x117BB30,1)[0]==0xF94017A9,
 'populate_entries18': words(0x117BB38,1)[0]==0xF9400D33,
 'populate_descriptor_table_a8': words(0x117BB68,1)[0]==0xF94056C8,
 'populate_calls_match': bl_target(0x117BB74,words(0x117BB74,1)[0])==0x11A2D4C,
 'populate_stores_candidate_child0': words(0x117BB7C,1)[0]==0xF9000359,
 'match_requires_candidate118': words(0x11A2D6C,1)[0]==0xF9408E68,
}
for k,v in chain.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(chain.values()): sys.exit(1)
print('R269_SOURCE_VERIFY=PASS')
