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
 'core_calls_r270_only':'return nsc::InstallR270MatcherFallbackCompareTrace();' in CORE and 'return nsc::InstallR269BaseVisualPopulationTrace();' not in CORE,
 'public_decl':'bool InstallR270MatcherFallbackCompareTrace();' in HPP,
 'ready_marker':'[NSC:R270] READY' in CPP,
 'compare_marker':'[NSC:R270] FALLBACK_COMPARE' in CPP,
 'compare_fields':all(x in CPP for x in ['desc_key=0x%08x','desc_type=%u','cand_key=0x%08x','cand_type=%u','key_equal=%u','type_equal=%u']),
 'readonly_flags':all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
 'inline_install':'R270FallbackCompareCaptureHook::InstallAtOffset(kR270FallbackCompareCaptureOffset);' in CPP,
 'offset_compare':'kR270FallbackCompareCaptureOffset   = 0x11A2E34' in CPP,
 'exact_replay':'ctx->W[8] = static_cast<uint32_t>(desc_type);' in CPP,
 'no_duplicate_getter_calls':'dfn50' not in CPP[CPP.find('HOOK_DEFINE_INLINE(R270FallbackCompareCaptureHook)'):CPP.find('// R269: exact population chain')],
 'workflow_verify':'python3 verify_r270.py' in WF,
 'workflow_artifact':'NSC2Switch-R270-MATCHER-FALLBACK-COMPARE-TRACE' in WF,
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
 'visual_populate_fingerprint':(0x117BA00,[0xD10383FF,0xFD003BE8,0xA9087BFD,0xA9096FFC,0xA90A67FA,0xA90B5FF8,0xA90C57F6,0xA90D4FF4]),
 'candidate_match_fingerprint':(0x11A2D4C,[0xA9BE57FE,0xA9014FF4,0xAA0003F3,0xF9400C00,0xAA0103F4,0xF9400008,0xF9400D08,0xD63F0100]),
 'source_link_fingerprint':(0x117D390,[0xF900C401,0xD65F03C0,0xF940C408,0xB4000068,0x52800020,0xD65F03C0,0xF9401408,0xB4000128]),
 'fallback_compare_capture_fingerprint':(0x11A2E34,[0x39401288,0x39401009,0x6B09011F,0x540001A1,0xB9400288,0xB9400009]),
}
for name,(off,exp) in expected.items():
    ok=words(off,len(exp))==exp
    print(f'{name}={"PASS" if ok else "FAIL"}')
    if not ok: sys.exit(1)
chain={
 'populate_calls_match': bl_target(0x117BB74,words(0x117BB74,1)[0])==0x11A2D4C,
 'match_descriptor_vcall50': words(0x11A2E14,2)==[0xF9402908,0xD63F0100],
 'match_saves_descriptor_record': words(0x11A2E1C,1)[0]==0xAA0003F4,
 'match_candidate18_load': words(0x11A2E20,1)[0]==0xF9400E60,
 'match_candidate_vcall50': words(0x11A2E2C,2)==[0xF9402908,0xD63F0100],
 'capture_is_descriptor_type_load': words(0x11A2E34,1)[0]==0x39401288,
 'next_is_candidate_type_load': words(0x11A2E38,1)[0]==0x39401009,
 'then_type_compare': words(0x11A2E3C,2)==[0x6B09011F,0x540001A1],
 'then_key_compare': words(0x11A2E44,3)==[0xB9400288,0xB9400009,0x6B09011F],
}
for k,v in chain.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(chain.values()): sys.exit(1)
print('R270_SOURCE_VERIFY=PASS')
