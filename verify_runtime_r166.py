#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,struct,sys
try:
    import lz4.block
except Exception:
    lz4=None

root=Path(__file__).resolve().parent
rt=(root/'overlay/source/program/nsc_runtime_v2.cpp').read_text()
h=(root/'overlay/source/program/nsc_runtime_v2.hpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
prep=(root/'prepare_exlaunch.sh').read_text()
wf=(root/'.github/workflows/build-runtime-r166.yml').read_text()
sfx=(root/'overlay/source/program/nsc_sfx_list_generated.hpp').read_text()

checks={
 'main_order': main.index('InstallResolverHookMigrationProbe();') < main.index('InstallOriginalMainRuntimePatches()') < main.index('InstallP128AStaticPreciseGateCaveProof();') < main.index('InstallR165Event150VoiceReadOnlyProbe();') < main.index('InstallR166SoundDispatchReadOnlyProbe();') < main.index('InstallV2MStageSafeTraceHooks();') < main.index('InstallV2NStageRegistryProof();') < main.index('InstallV2PPassiveOrderProbe();'),
 'fail_closed_main': 'if (!nsc::v2::InstallOriginalMainRuntimePatches()) return;' in main,
 'thirty_word_plan': 'WordPatch plan[30]' in rt and 'condition_words=5 p67_words=1 p128_words=24' in rt,
 'validate_before_write': rt.index('Validate ALL original words before the first write') < rt.index('patcher.Write<std::uint32_t>'),
 'paired_file_disabled': 'paired_main_file=0' in rt,
 'resolver_7_markers': '[NSC:V2D] RESOLVER_READY' in rt and '[NSC:V2D] RUNTIME_PATCH_READY' in rt,
 'workflow_only_r166': len(list((root/'.github/workflows').glob('*.yml')))==1 and 'NSC-RUNTIME-R166-sound1030-readonly-probe' in wf,
 'workflow_original_main': 'original/atmosphere/contents/0100FA10190A0000/exefs/main' in wf,
 'workflow_not_reference_main': 'reference_p128/atmosphere/contents/0100FA10190A0000/exefs/main" "$OUT/atmosphere' not in wf,
 'prepare_r166_elf': 'runtime_r166.elf' in prep,
 'no_char281_runtime': 'char_id == 281' not in bridge and 'char==281' not in bridge and 'char = 281' not in bridge,
 'p128_retained': '[NSC:P128A] READY' in bridge and 'no_force708=1' in bridge and 'no_force710=1' in bridge,
 'op23_safe': '[NSC:V2H] OP23_SAFE_SUPPRESS' in bridge and 'call_766320=0' in bridge and 'playaction_wrapper=0' in bridge,
 'stage_actor_enemy_parity': '[NSC:V2I] STAGE2_PARITY' in bridge and 'fix_actor=1 fix_enemy=%u poststage=0 pc_source_parity=1' in bridge,
 'no_manual_poststage_stagebridge': 'reinterpret_cast<VoidFn>(base + kPostStageOffset)();' not in bridge,
 'op26_playback_retained': '[NSC:V2I] OP26_PLAY' in bridge and 'native_813d88_contract=1' in bridge and 'vtable[0x1030 / sizeof(void*)]' in bridge,
 'v2m_graph': '[NSC:V2M] STAGE_GRAPH' in bridge and 'fresh_resolve=1 stale_pointer_deref=0 readonly=1' in bridge,
 'v2m_resource_trace': '[NSC:V2M] STAGE_TRACE_ARM' in bridge and '[NSC:V2M] STAGE_TRACE_DISARM' in bridge,
 'v2m_hooks_passive': 'poststage_observe_only=1' in bridge and 'manual_poststage_call=0' in bridge,
 'v2n_registry_constants': all(x in bridge for x in ('kStageRuntimeRootOffset      = 0x2143488','kStageRegistryLookupOffset   = 0x8364F8','kStageRegistryOwnerOffset    = 0x6C10','kStageRegistryMapOffset      = 0x148')),
 'v2n_registry_probe': '[NSC:V2N] STAGE_REGISTRY' in bridge and 'readonly_lookup=1 insert=0 mutation=0' in bridge,
 'v2n_pre_post': 'V2NProbeStageRegistry("pre_specific"' in bridge and 'V2NProbeStageRegistry("post_specific"' in bridge,
 'v2p_ready': '[NSC:V2P] READY stageinfo_cpk_order_probe=1 passive_only=1' in bridge,
 'v2p_stageinfo_pre': '[NSC:V2P] STAGEINFO_LOAD_REQ phase=pre' in bridge,
 'v2p_stageinfo_post': '[NSC:V2P] STAGEINFO_LOAD_REQ phase=post' in bridge,
 'v2p_cpk_bound': '[NSC:V2P] CPK_BOUND' in bridge and 'g_v2p_cpk_bound_success' in bridge,
 'v2p_exact_stageinfo_paths': 'data/stage/StageInfo.bin.xfbin' in bridge and 'data/stage/AdvStageInfo.bin.xfbin' in bridge,
 'v2p_no_reindex': '[NSC:V2O]' not in bridge and 'STAGE_REINDEX' not in bridge and 'kStageInfoReloadOffset' not in bridge and 'ReloadFn' not in bridge,
 'v2p_no_direct_loader_call': '0x835FAC' not in bridge and '0x835fac' not in bridge,
 'v2p_no_new_stageinfo_trampoline': 'StageInfoHook' not in bridge and 'StageInfoLoaderHook' not in bridge,
 'r165_event150_offset': 'kEvent150Offset           = 0x813ECC' in bridge,
 'r165_mevoice_offset': 'kNativeMeVoiceOffset      = 0x813D88' in bridge,
 'r165_event150_hook': '[NSC:R165] EVT150 phase=pre' in bridge and '[NSC:R165] EVT150 phase=post' in bridge,
 'r165_native_voice_hook': '[NSC:R165] ME_VOICE phase=pre' in bridge and '[NSC:R165] ME_VOICE phase=post' in bridge,
 'r165_readonly_ready': '[NSC:R165] READY installed=1' in bridge and 'voice_mutation=0' in bridge and 'sound_registry_mutation=0' in bridge,
 'r165_no_play_in_probe': 'R165Event150ProbeHook' in bridge and 'R165NativeMeVoiceProbeHook' in bridge,
 'r165_called_from_main': 'InstallR165Event150VoiceReadOnlyProbe();' in main,
 'r166_sound_offset': 'kSoundDispatch1030Offset   = 0x635DA0' in bridge,
 'r166_sound_hook': '[NSC:R166] SOUND1030 phase=pre' in bridge and '[NSC:R166] SOUND1030 phase=post' in bridge,
 'r166_readonly_ready': '[NSC:R166] READY installed=1' in bridge and 'capture_all_custom_commands=1' in bridge and 'voice_mutation=0' in bridge and 'registry_mutation=0' in bridge,
 'r166_called_from_main': 'InstallR166SoundDispatchReadOnlyProbe();' in main,
 'sfx_count_160': 'kCount = 160' in sfx,
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
orig_sha=sha(orig); ref_sha=sha(ref)
print('original_main_sha256',orig_sha)
print('reference_p128_main_sha256',ref_sha)
if orig_sha!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9': sys.exit(1)
if ref_sha!='904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff': sys.exit(1)
va_o,o=decode_text(orig); va_r,r=decode_text(ref)
if va_o!=0 or va_r!=0 or len(o)!=len(r): sys.exit(1)
diff={off:(struct.unpack_from('<I',o,off)[0],struct.unpack_from('<I',r,off)[0])
      for off in range(0,len(o)-3,4)
      if struct.unpack_from('<I',o,off)[0]!=struct.unpack_from('<I',r,off)[0]}
print('text_diff_words',len(diff))
if len(diff)!=30: sys.exit(1)
expected={
0x747878:(0x52804009,0x528040A9),0x7774DC:(0x7108031F,0x7108171F),
0x777770:(0x7108027F,0x7108167F),0x777938:(0x7108027F,0x7108167F),
0x777A6C:(0x7108027F,0x7108167F),0x7F2A9C:(0xBD001FE0,0xD503201F),
0x77C480:(0x54000B81,0x1400000E),0x77C494:(0x34000AC0,0xD503201F),
0x77C4A8:(0x34000A20,0xD503201F),0x77C4B4:(0x34000300,0x14000018),
0x77C4B8:(0xF0009619,0x7100291F),0x77C4BC:(0x913C2339,0x54000220),
0x77C4C0:(0xAA1903E0,0x71002D1F),0x77C4C4:(0x942A6437,0x540001E0),
0x77C4C8:(0xF9400268,0x71003D1F),0x77C4CC:(0xAA1303E0,0x54000181),
0x77C4D0:(0xF9402508,0xB94E56EA),0x77C4D4:(0xD63F0100,0x7104615F),
0x77C4D8:(0x11000401,0x54000129),0x77C4DC:(0xB0009680,0x7140055F),
0x77C4E0:(0x91292C00,0x540000E2),0x77C4E4:(0x942A642F,0xF9410EEA),
0x77C4E8:(0xF94002E8,0xB40000AA),0x77C4EC:(0xAA1703E0,0xB9402D4A),
0x77C4F0:(0xF9402508,0x710B0D5F),0x77C4F4:(0xD63F0100,0x54000041),
0x77C4F8:(0x11000401,0x14000002),0x77C4FC:(0xB0009940,0x1400003D),
0x77C500:(0x91086800,0x17FFFFE1),0x77C520:(0xB40003E0,0x1400001F),}
if diff!=expected:
    print('reference_delta_exact_30_words FAIL');sys.exit(1)
print('reference_delta_exact_30_words PASS')

# Registry lookup fingerprint used by V2N.
reg=[struct.unpack_from('<I',o,0x8364F8+4*i)[0] for i in range(8)]
reg_expected=[0xF8408C09,0xB40001A9,0xAA0003E8,0xB940212A,0x6B01015F,0x1A9F27EA,0x9A893108,0xF86A5929]
print('stage_registry_fingerprint','PASS' if reg==reg_expected else 'FAIL')
if reg!=reg_expected:sys.exit(1)

# Offline resolver signatures remain unique in original main.
def parse_arr(name):
    m=re.search(rf'{re.escape(name)}\[\]\s*=\s*\{{([^}}]+)\}};',rt,re.S)
    if not m: raise RuntimeError('missing '+name)
    return [int(x,16) for x in re.findall(r'0x[0-9A-Fa-f]+',m.group(1))]
def scan(text,vals,masks):
    out=[]; limit=len(text)-4*len(vals)+1
    if masks[0]==0xFFFFFFFF:
        needle=struct.pack('<I',vals[0]); pos=text.find(needle)
        while pos!=-1:
            if pos%4==0 and pos<limit and all((struct.unpack_from('<I',text,pos+4*i)[0]&m)==(v&m) for i,(v,m) in enumerate(zip(vals,masks))):out.append(pos)
            pos=text.find(needle,pos+1)
        return out
    for off in range(0,limit,4):
        if all((struct.unpack_from('<I',text,off+4*i)[0]&m)==(v&m) for i,(v,m) in enumerate(zip(vals,masks))):out.append(off)
    return out
specs=[('CHARACODE_GETTER','kCharVal','kCharMask',0x3F4150),('CPK_BIND','kCpkVal','kCpkMask',0x473190),('EVENT236','kEvent236Val','kEvent236Mask',0x816300),('PLAY_ACTION','kPlayVal','kPlayMask',0x766B8C),('CENTRAL_SETTER','kSetterVal','kSetterMask',0x766320),('UJ_SESSION_OUTER','kOuterVal','kOuterMask',0x7EF098),('STATE137_CONTROLLER','kState137Val','kState137Mask',0x7E6EA8)]
for name,vn,mn,exp in specs:
    hits=scan(o,parse_arr(vn),parse_arr(mn)); ok=hits==[exp]
    print('offline_original_'+name,'PASS' if ok else 'FAIL','hits='+','.join(hex(x) for x in hits[:4]))
    if not ok:sys.exit(1)

# Exact R165 handler fingerprints in original text.
e150=[struct.unpack_from('<I',o,0x813ECC+4*i)[0] for i in range(8)]
e150_exp=[0xD101C3FF,0xA90557FE,0xA9064FF4,0x9000C988,0xF9426108,0xF9400108,0xB94A9108,0x7100311F]
mev=[struct.unpack_from('<I',o,0x813D88+4*i)[0] for i in range(8)]
mev_exp=[0xF81F0FFE,0x79C04828,0x11401D01,0xF9400008,0xF9481908,0x2A1F03E2,0xD63F0100,0x52800020]
print('r165_event150_fingerprint','PASS' if e150==e150_exp else 'FAIL')
print('r165_mevoice_fingerprint','PASS' if mev==mev_exp else 'FAIL')
if e150!=e150_exp or mev!=mev_exp:sys.exit(1)

snd=[struct.unpack_from('<I',o,0x635DA0+4*i)[0] for i in range(8)]
snd_exp=[0xA9BE57FE,0xA9014FF4,0xF9400008,0x2A0203F4,0x2A0103F3,0xAA0003F5,0xF9462508,0xD63F0100]
print('r166_sound1030_fingerprint','PASS' if snd==snd_exp else 'FAIL')
if snd!=snd_exp:sys.exit(1)
print('NSC_RUNTIME_R166_SOURCE_VERIFY=PASS')
