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
 'core_calls_r268_only':'return nsc::InstallR268BaseVisualChildGateTrace();' in CORE and 'return nsc::InstallR267SecondaryInnerBaseDrawTrace();' not in CORE,
 'public_decl':'bool InstallR268BaseVisualChildGateTrace();' in HPP,
 'ready_marker':'[NSC:R268] READY' in CPP,
 'visual_list_marker':'[NSC:R268] VISUAL_LIST_PRE' in CPP and '[NSC:R268] VISUAL_LIST_POST' in CPP,
 'entry_marker':'[NSC:R268] VISUAL_ENTRY' in CPP,
 'child_gate_marker':'[NSC:R268] CHILD_GATE' in CPP,
 'child_draw_marker':'[NSC:R268] CHILD_DRAW' in CPP,
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'r268_installs':sum(CPP.count(x+'::InstallAtOffset') for x in ['R268BaseVisualListHook','R268VisualChildGateHook','R268VisualChildDrawHook'])==3,
 'offset_visual_list':'kR267BaseVisualDrawOffset         = 0x117E0D8' in CPP,
 'offset_child_gate':'kR268VisualChildGateOffset        = 0x11A3E3C' in CPP,
 'offset_child_draw':'kR268VisualChildDrawOffset        = 0x11A2444' in CPP,
 'workflow_verify':'python3 verify_r268.py' in WF,
 'workflow_artifact':'NSC2Switch-R268-BASE-VISUAL-CHILD-GATE-TRACE' in WF,
 'workflow_no_main':'test ! -e out/runtime/atmosphere/contents/0100FA10190A0000/exefs/main' in WF,
}
for k,vv in checks.items(): print(f'{k}={"PASS" if vv else "FAIL"}')
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
 'base_visual_list_fingerprint':(0x117E0D8,[0xA9BE57FE,0xA9014FF4,0xF9401408,0xB4000288,0x79404109,0x34000249,0x52800D0A,0x9B0A7D29]),
 'child_gate_fingerprint':(0x11A3E3C,[0xF81E0FFE,0xA9014FF4,0x394B9008,0x37100088,0xA9414FF4,0xF84207FE,0xD65F03C0,0xF9400008]),
 'child_draw_fingerprint':(0x11A2444,[0xA9BA7BFD,0xA9016FFC,0xA90267FA,0xA9035FF8,0xA90457F6,0xA9054FF4,0xD14007FF,0xD10183FF]),
}
for name,(off,exp) in expected.items():
    ok=words(off,len(exp))==exp
    print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok: sys.exit(1)
chain={
 'visual_load_list28':words(0x117E0E0,1)[0]==0xF9401408,
 'visual_count20':words(0x117E0E8,1)[0]==0x79404109,
 'visual_entries18':words(0x117E104,1)[0]==0xF9400D08,
 'visual_entry_stride_68':words(0x117E120,1)[0]==0x9101A294,
 'visual_calls_child_gate':bl_target(0x117E110,words(0x117E110,1)[0])==0x11A3E3C,
 'child_gate_flag2e4':words(0x11A3E44,1)[0]==0x394B9008,
 'child_gate_bit2_branch':words(0x11A3E48,1)[0]==0x37100088,
 'child_gate_fn30_load':words(0x11A3E60,1)[0]==0xF9401908,
 'child_gate_byte125':words(0x11A3E6C,1)[0]==0x39449668,
 'child_gate_calls_child_draw':bl_target(0x11A3E78,words(0x11A3E78,1)[0])==0x11A2444,
}
for k,vv in chain.items(): print(f'{k}={"PASS" if vv else "FAIL"}')
if not all(chain.values()): sys.exit(1)
print('R268_SOURCE_VERIFY=PASS')
