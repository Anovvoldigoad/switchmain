#!/usr/bin/env python3
from pathlib import Path
import hashlib,struct,sys
try:
    import lz4.block
except Exception:
    lz4=None
root=Path(__file__).resolve().parent
rt=(root/'overlay/source/program/nsc_runtime_v2.cpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hdr=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
prep=(root/'prepare_exlaunch.sh').read_text()
wfs=list((root/'.github/workflows').glob('*.yml'))
wf=wfs[0].read_text() if len(wfs)==1 else ''
checks={
 'main_order': main.index('InstallResolverHookMigrationProbe();') < main.index('InstallOriginalMainRuntimePatches()') < main.index('InstallP128AStaticPreciseGateCaveProof();') < main.index('InstallR172UjMissAnmDirectParity();') < main.index('InstallR173DpadRouteTrace();') < main.index('InstallV2NStageRegistryProof();'),
 'fail_closed_main':'if (!nsc::v2::InstallOriginalMainRuntimePatches()) return;' in main,
 'r171_not_installed':'InstallR171Uj707Flag70Release();' not in main and 'ActionGateFlagReleaseHook::InstallAtOffset' not in bridge,
 'r172_installed':'InstallR172UjMissAnmDirectParity();' in main and 'bool InstallR172UjMissAnmDirectParity();' in hdr,
 'r173_installed':'InstallR173DpadRouteTrace();' in main and 'void InstallR173DpadRouteTrace();' in hdr,
 'r173_ready':'[NSC:R173] READY dpad_route_trace=1' in bridge,
 'r173_markers':'[NSC:R173] DPAD_ROUTE_%s' in bridge,
 'r173_callsites':'caller_off == 0x646CFC' in bridge and 'caller_off == 0x647080' in bridge,
 'r173_indexes':'index == 921' in bridge and 'index == 928' in bridge,
 'r173_snapshot':all(x in bridge for x in ('pb + 0x12B78','pb + 0x12B7C','pb + 0x12B80','pb + 0x12B84','pb + 0x12B88','pb + 0xF30','pb + 0xBDA8')),
 'r173_zero_extra_hook':'zero_extra_trampoline=1' in bridge and 'reuse_playaction_hook=1' in bridge,
 'r173_no_char281_guard':'char_id == 281' not in bridge,
 'r173_no_dpad_write':'no_state_write=1 dpad_change=0' in bridge,
 'r172_ready':'[NSC:R172] READY parity=1 direct_off=0x766320' in bridge,
 'r172_direct_call':'reinterpret_cast<DirectAnmFn>(base + kCentralActionSetterOffset)' in bridge,
 'r172_default_abi':'target, static_cast<int32_t>(index), -1, 0, 1.0f' in bridge,
 'r172_guard':all(x in bridge for x in ('param2 == 0','side == 0u','semantic && member','anm1268_before == 707u','state1268_after_pre == 707u','param3 == 8')),
 'r172_no_char281_guard':'char_id == 281' not in bridge,
 'r172_no_ixn0_guard':'strcmp(text, "IXN0")' not in bridge and 'StringEquals(text, "IXN0")' not in bridge,
 'r172_other_op23_failclosed':'[NSC:V2H] OP23_SAFE_SUPPRESS' in bridge and 'setanmdirect_deferred_non_uj=1' in bridge,
 'r172_no_force':'force708=0 force710=0 force74=0 force77=0' in bridge,
 'stage_trace_hooks_omitted':'InstallV2MStageSafeTraceHooks();' not in main,
 'voice_probes_not_installed':'InstallR165Event150VoiceReadOnlyProbe();' not in main and 'InstallR166SoundDispatchReadOnlyProbe();' not in main,
 'p128_retained':'[NSC:P128A] READY' in bridge and 'no_force708=1' in bridge and 'no_force710=1' in bridge,
 'thirty_word_plan':'WordPatch plan[30]' in rt and 'condition_words=5 p67_words=1 p128_words=24' in rt,
 'validate_before_write':rt.index('Validate ALL original words before the first write') < rt.index('patcher.Write<std::uint32_t>'),
 'workflow_r173':len(wfs)==1 and 'NSC-RUNTIME-R173-dpad-route-trace' in wf,
 'prepare_r173_elf':'runtime_r173.elf' in prep,
}
for k,v in checks.items(): print(k,'PASS' if v else 'FAIL')
if not all(checks.values()): sys.exit(1)

def decode_text(path):
    b=path.read_bytes()
    if b[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',b,o)[0]
    flags=u(0x0c);fo=u(0x10);va=u(0x14);size=u(0x18);csz=u(0x60)
    blob=b[fo:fo+(csz if flags&1 else size)]
    if flags&1:
        if lz4 is None: raise RuntimeError('lz4 required')
        blob=lz4.block.decompress(blob,uncompressed_size=size)
    return va,blob
orig=root/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
ref=root/'reference_p128/atmosphere/contents/0100FA10190A0000/exefs/main'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if sha(orig)!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9':
    print('original_main_sha256 FAIL');sys.exit(1)
print('original_main_sha256 PASS')
va_o,o=decode_text(orig);va_r,r=decode_text(ref)
if va_o!=0 or va_r!=0 or len(o)!=len(r): sys.exit(1)
diff={off:(struct.unpack_from('<I',o,off)[0],struct.unpack_from('<I',r,off)[0]) for off in range(0,len(o)-3,4) if struct.unpack_from('<I',o,off)[0]!=struct.unpack_from('<I',r,off)[0]}
print('reference_delta_30_words','PASS' if len(diff)==30 else 'FAIL',len(diff))
if len(diff)!=30:sys.exit(1)
def words(off,n):return [struct.unpack_from('<I',o,off+4*i)[0] for i in range(n)]
# 0x766320 exact ABI/prologue fingerprint
setter=[0xD10303FF,0x6D0523E9,0xA9067BFD,0xA9076FFC,0xA90867FA,0xA9095FF8,0xA90A57F6,0xA90B4FF4,0xF9410C08,0x4EA01C08,0x2A0303F4,0x2A0203F6,0xAA0003F3,0x2A0103F5]
# companion getter: current animation from actor+0x218 -> +0x2C, fallback74
getter=[0xF9410C08,0xB4000068,0xB9402D00,0xD65F03C0,0x52800940,0xD65F03C0]
# setter tail proves W21 (incoming W1) is written to actor+0x1268.
writer=[0xB9126668,0x1E380008,0xB9127268,0xF9410E68,0xB9126A75,0xBD126E68,0xB9127674,0xB900311F]
# Native direct callsite feeds index936, -1, 0, rate1 into 0x766320.
call936=[0x1E2E1000,0x52807501,0x12800002,0xAA1303E0,0x2A1F03E3,0x941BB21D]
for name,got,exp in [
 ('r172_setter_fingerprint',words(0x766320,len(setter)),setter),
 ('r172_animation_getter_fingerprint',words(0x766A98,len(getter)),getter),
 ('r172_animation_writer_fingerprint',words(0x766A50,len(writer)),writer),
 ('r172_native_direct_callsite_fingerprint',words(0x79A98,len(call936)),call936),
]:
    ok=got==exp;print(name,'PASS' if ok else 'FAIL')
    if not ok:sys.exit(1)
reg=[0xF8408C09,0xB40001A9,0xAA0003E8,0xB940212A,0x6B01015F,0x1A9F27EA,0x9A893108,0xF86A5929]
ok=words(0x8364F8,8)==reg
print('stage_registry_fingerprint','PASS' if ok else 'FAIL')
if not ok:sys.exit(1)
print('NSC_RUNTIME_R173_SOURCE_VERIFY=PASS')
