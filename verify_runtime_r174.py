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
 'main_order': main.index('InstallResolverHookMigrationProbe();') < main.index('InstallOriginalMainRuntimePatches()') < main.index('InstallP128AStaticPreciseGateCaveProof();') < main.index('InstallR172UjMissAnmDirectParity();') < main.index('InstallR174DpadSelectorTrace();') < main.index('InstallV2NStageRegistryProof();'),
 'fail_closed_main':'if (!nsc::v2::InstallOriginalMainRuntimePatches()) return;' in main,
 'r171_not_installed':'InstallR171Uj707Flag70Release();' not in main and 'ActionGateFlagReleaseHook::InstallAtOffset' not in bridge,
 'r172_installed':'InstallR172UjMissAnmDirectParity();' in main and 'bool InstallR172UjMissAnmDirectParity();' in hdr,
 'r174_installed':'InstallR174DpadSelectorTrace();' in main and 'void InstallR174DpadSelectorTrace();' in hdr,
 'r174_ready':'[NSC:R174] READY dpad_selector_trace=1' in bridge,
 'r174_markers':'[NSC:R174] DPAD_SELECTOR_%s' in bridge,
 'r174_callsites':'caller_off == 0x646CFC' in bridge and 'caller_off == 0x647080' in bridge,
 'r174_indexes':'index == 921' in bridge and 'index == 928' in bridge,
 'r174_selector_offsets':all(x in bridge for x in ('pb + 0x12264','pb + 0x12268','pb + 0x1223C','pb + 0x105F8','pb + 0x105FC','pb + 0x10600','pb + 0x10610')),
 'r174_candidate_table':all(x in bridge for x in ('case 0u: base_candidate = 923u','case 1u: base_candidate = 924u','case 2u: base_candidate = 921u','case 3u: base_candidate = 922u')),
 'r174_fallback_flag':'fallback921_suspect' in bridge and 'base_candidate != 921u' in bridge,
 'r174_zero_extra_hook':'zero_extra_trampoline=1' in bridge and 'reuse_playaction_hook=1' in bridge,
 'r174_no_char281_guard':'char_id == 281' not in bridge,
 'r174_no_dpad_write':'no_state_write=1 dpad_change=0' in bridge,
 'r172_direct_call':'reinterpret_cast<DirectAnmFn>(base + kCentralActionSetterOffset)' in bridge,
 'r172_guard':all(x in bridge for x in ('param2 == 0','side == 0u','semantic && member','anm1268_before == 707u','state1268_after_pre == 707u','param3 == 8')),
 'r172_other_op23_failclosed':'[NSC:V2H] OP23_SAFE_SUPPRESS' in bridge and 'setanmdirect_deferred_non_uj=1' in bridge,
 'stage_trace_hooks_omitted':'InstallV2MStageSafeTraceHooks();' not in main,
 'voice_probes_not_installed':'InstallR165Event150VoiceReadOnlyProbe();' not in main and 'InstallR166SoundDispatchReadOnlyProbe();' not in main,
 'p128_retained':'[NSC:P128A] READY' in bridge and 'no_force708=1' in bridge and 'no_force710=1' in bridge,
 'thirty_word_plan':'WordPatch plan[30]' in rt and 'condition_words=5 p67_words=1 p128_words=24' in rt,
 'validate_before_write':rt.index('Validate ALL original words before the first write') < rt.index('patcher.Write<std::uint32_t>'),
 'workflow_r174':len(wfs)==1 and 'NSC-RUNTIME-R174-dpad-selector-fallback-trace' in wf,
 'prepare_r174_elf':'runtime_r174.elf' in prep,
}
for k,v in checks.items(): print(k,'PASS' if v else 'FAIL')
if not all(checks.values()): sys.exit(1)

def decode_nso(path):
    b=path.read_bytes()
    if b[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',b,o)[0]
    flags=u(0x0c)
    secs=[]
    for bit,foff,moff,usize,cszoff in [
        (0,0x10,0x14,0x18,0x60),
        (1,0x20,0x24,0x28,0x64),
        (2,0x30,0x34,0x38,0x68),
    ]:
        fo,mo,sz,csz=u(foff),u(moff),u(usize),u(cszoff)
        blob=b[fo:fo+(csz if flags&(1<<bit) else sz)]
        if flags&(1<<bit):
            if lz4 is None: raise RuntimeError('lz4 required')
            blob=lz4.block.decompress(blob,uncompressed_size=sz)
        secs.append((mo,blob))
    return secs

orig=root/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
ref=root/'reference_p128/atmosphere/contents/0100FA10190A0000/exefs/main'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if sha(orig)!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9':
    print('original_main_sha256 FAIL');sys.exit(1)
print('original_main_sha256 PASS')
secs_o=decode_nso(orig);secs_r=decode_nso(ref)
text_o=secs_o[0][1];text_r=secs_r[0][1]
diff={off:(struct.unpack_from('<I',text_o,off)[0],struct.unpack_from('<I',text_r,off)[0]) for off in range(0,len(text_o)-3,4) if struct.unpack_from('<I',text_o,off)[0]!=struct.unpack_from('<I',text_r,off)[0]}
print('reference_delta_30_words','PASS' if len(diff)==30 else 'FAIL',len(diff))
if len(diff)!=30:sys.exit(1)

def words(off,n):return [struct.unpack_from('<I',text_o,off+4*i)[0] for i in range(n)]
setter=[0xD10303FF,0x6D0523E9,0xA9067BFD,0xA9076FFC,0xA90867FA,0xA9095FF8,0xA90A57F6,0xA90B4FF4,0xF9410C08,0x4EA01C08,0x2A0303F4,0x2A0203F6,0xAA0003F3,0x2A0103F5]
if words(0x766320,len(setter))!=setter:
    print('r172_setter_fingerprint FAIL');sys.exit(1)
print('r172_setter_fingerprint PASS')

# R174 exact native selector/fallback proof.
controller=[0x52809688,0x72A00028,0xAA0003F3,0x8B080017]
if words(0x6461D4,4)!=controller:
    print('r174_controller_base_fingerprint FAIL');sys.exit(1)
print('r174_controller_base_fingerprint PASS')

fallback=[0xAA1303E0,0x2A1403E1,0x52800022,0x9404886C,0x1E2E1000,0xF100001F,0x52807328,0x1A940101,0x12800002,0xAA1303E0,0x2A1F03E3,0x2A1F03E4,0x94047FA5]
if words(0x646CC8,len(fallback))!=fallback:
    print('r174_native_fallback_fingerprint FAIL');sys.exit(1)
print('r174_native_fallback_fingerprint PASS')

lookup=[0xA9BE57FE,0xA9014FF4,0xB94E5408,0x2A0203F5,0x2A0103F3,0xAA0003F4]
if words(0x768E84,len(lookup))!=lookup:
    print('r174_action_lookup_fingerprint FAIL');sys.exit(1)
print('r174_action_lookup_fingerprint PASS')

# mode table @ rodata VA 0x1B29960
ro_base,ro=secs_o[1]
va=0x1B29960
if not (ro_base <= va < ro_base+len(ro)):
    print('r174_candidate_table_range FAIL');sys.exit(1)
table=struct.unpack_from('<4I',ro,va-ro_base)
print('r174_candidate_table',table)
if table!=(923,924,921,922):
    print('r174_candidate_table FAIL');sys.exit(1)
print('r174_candidate_table PASS')

reg=[0xF8408C09,0xB40001A9,0xAA0003E8,0xB940212A,0x6B01015F,0x1A9F27EA,0x9A893108,0xF86A5929]
if words(0x8364F8,8)!=reg:
    print('stage_registry_fingerprint FAIL');sys.exit(1)
print('stage_registry_fingerprint PASS')
print('NSC_RUNTIME_R174_SOURCE_VERIFY=PASS')
