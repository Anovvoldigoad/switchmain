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
 'core_calls_r267_only':'return nsc::InstallR267SecondaryInnerBaseDrawTrace();' in CORE and 'InstallR266RenderRegistrationProducerTrace();' not in CORE,
 'public_decl':'bool InstallR267SecondaryInnerBaseDrawTrace();' in HPP,
 'ready_marker':'[NSC:R267] READY' in CPP,
 'bind_marker':'[NSC:R267] INNER_BIND_PRE' in CPP and '[NSC:R267] INNER_BIND_POST' in CPP,
 'base_draw_marker':'[NSC:R267] BASE_DRAW_PRE' in CPP,
 'visual_marker':'[NSC:R267] BASE_VISUAL_DRAW' in CPP,
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'three_r267_installs':sum(CPP.count(x+'::InstallAtOffset') for x in ['R267SecondaryInnerBindHook','R267BaseModelDrawHook','R267BaseVisualDrawHook'])==3,
 'offset_bind':'kR267SecondaryInnerBindOffset     = 0x118001C' in CPP,
 'offset_base_draw':'kR267BaseModelDrawOffset          = 0x6ECAE4' in CPP,
 'offset_visual':'kR267BaseVisualDrawOffset         = 0x117E0D8' in CPP,
 'workflow_verify':'python3 verify_r267.py' in WF,
 'workflow_artifact':'NSC2Switch-R267-SECONDARY-INNER-BASE-DRAW-TRACE' in WF,
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
 'inner_bind_fingerprint':(0x118001C,[0x7941B428,0x79007008,0xB9003C02,0xB9408828,0xB9004008,0x52A7F008,0xB9004808,0xF9400428]),
 'base_visual_draw_fingerprint':(0x117E0D8,[0xA9BE57FE,0xA9014FF4,0xF9401408,0xB4000288,0x79404109,0x34000249,0x52800D0A,0x9B0A7D29]),
}
for name,(off,exp) in expected.items():
    ok=words(off,len(exp))==exp
    print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok: sys.exit(1)
# Exact static chain: model draw calls visual draw only after secondary+0x18 non-null.
chain={
 'base_draw_secondary98_load':words(0x6ECAF0,1)[0]==0xF9404C00,
 'base_draw_inner18_load':words(0x6ECB10,1)[0]==0xF9400C08,
 'base_draw_inner18_null_skip':words(0x6ECB14,1)[0]==0xB40000C8,
 'base_draw_visual_call':bl_target(0x6ECB18,words(0x6ECB18,1)[0])==0x117E0D8,
 'inner_bind_source_plus8':words(0x1180038,1)[0]==0xF9400428,
 'inner_bind_store_plus18':words(0x118003C,1)[0]==0xF9000C08,
 'derived_setup_calls_bind':bl_target(0x1182C68,words(0x1182C68,1)[0])==0x118001C,
}
for k,v in chain.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(chain.values()): sys.exit(1)
print('R267_SOURCE_VERIFY=PASS')
