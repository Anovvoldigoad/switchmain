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
wf=(root/'.github/workflows/build-runtime-r167.yml').read_text()
sfx=(root/'overlay/source/program/nsc_sfx_list_generated.hpp').read_text()

checks={
 'main_order': main.index('InstallResolverHookMigrationProbe();') < main.index('InstallOriginalMainRuntimePatches()') < main.index('InstallP128AStaticPreciseGateCaveProof();') < main.index('InstallR167CustomUjMissAnimationRefresh();') < main.index('InstallV2MStageSafeTraceHooks();') < main.index('InstallV2NStageRegistryProof();') < main.index('InstallV2PPassiveOrderProbe();'),
 'fail_closed_main': 'if (!nsc::v2::InstallOriginalMainRuntimePatches()) return;' in main,
 'voice_probes_not_installed': 'InstallR165Event150VoiceReadOnlyProbe();' not in main and 'InstallR166SoundDispatchReadOnlyProbe();' not in main,
 'r167_ready_installed': 'InstallR167CustomUjMissAnimationRefresh();' in main and '[NSC:R167] READY custom_uj_miss_animation_refresh=1' in bridge,
 'r167_exact_filter': all(x in bridge for x in ('index == 74','a2 == -1','pre_action == 740u','caller_off == 0x798F34','pre_e80 == 1u','pre_bda4 == 1u')),
 'r167_semantic_custom_filter': 'const bool semantic_uj = custom && P64QuerySemanticUltimateJutsu(actor);' in bridge,
 'r167_single_native_call': 'const int32_t effective_a2 = r167_miss_refresh ? 0 : a2;' in bridge and 'Orig(actor, index, effective_a2, a3, a4, a5, rate)' in bridge and 'single_native_call=1' in bridge,
 'r167_markers': '[NSC:R167] UJ_MISS_ANM_REFRESH phase=pre' in bridge and '[NSC:R167] UJ_MISS_ANM_REFRESH phase=post' in bridge,
 'r167_no_char281_branch': 'char_id == 281' not in bridge and 'char==281' not in bridge and 'char = 281' not in bridge,
 'r167_no_voice_mutation': 'voice_probe=0 voice_mutation=0' in bridge,
 'thirty_word_plan': 'WordPatch plan[30]' in rt and 'condition_words=5 p67_words=1 p128_words=24' in rt,
 'validate_before_write': rt.index('Validate ALL original words before the first write') < rt.index('patcher.Write<std::uint32_t>'),
 'paired_file_disabled': 'paired_main_file=0' in rt,
 'resolver_7_markers': '[NSC:V2D] RESOLVER_READY' in rt and '[NSC:V2D] RUNTIME_PATCH_READY' in rt,
 'workflow_only_r167': len(list((root/'.github/workflows').glob('*.yml')))==1 and 'NSC-RUNTIME-R167-uj-miss-animation-refresh' in wf,
 'workflow_original_main': 'original/atmosphere/contents/0100FA10190A0000/exefs/main' in wf,
 'workflow_not_reference_main': 'reference_p128/atmosphere/contents/0100FA10190A0000/exefs/main" "$OUT/atmosphere' not in wf,
 'prepare_r167_elf': 'runtime_r167.elf' in prep,
 'p128_retained': '[NSC:P128A] READY' in bridge and 'no_force708=1' in bridge and 'no_force710=1' in bridge,
 'op23_safe': '[NSC:V2H] OP23_SAFE_SUPPRESS' in bridge and 'call_766320=0' in bridge and 'playaction_wrapper=0' in bridge,
 'stage_actor_enemy_parity': '[NSC:V2I] STAGE2_PARITY' in bridge and 'fix_actor=1 fix_enemy=%u poststage=0 pc_source_parity=1' in bridge,
 'no_manual_poststage_stagebridge': 'reinterpret_cast<VoidFn>(base + kPostStageOffset)();' not in bridge,
 'op26_playback_retained': '[NSC:V2I] OP26_PLAY' in bridge and 'native_813d88_contract=1' in bridge and 'vtable[0x1030 / sizeof(void*)]' in bridge,
 'v2m_graph': '[NSC:V2M] STAGE_GRAPH' in bridge and 'fresh_resolve=1 stale_pointer_deref=0 readonly=1' in bridge,
 'v2n_registry_probe': '[NSC:V2N] STAGE_REGISTRY' in bridge and 'readonly_lookup=1 insert=0 mutation=0' in bridge,
 'v2p_ready': '[NSC:V2P] READY stageinfo_cpk_order_probe=1 passive_only=1' in bridge,
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

# R167 static contracts in original v1.70 main.
def words(off,n):
    return [struct.unpack_from('<I',o,off+4*i)[0] for i in range(n)]
cleanup=words(0x798F1C,8)
cleanup_exp=[0x1E2E1000,0x12800002,0xAA1303E0,0x2A1F03E3,0x2A1F03E4,0x97FF3717,0xB94E5668,0x7100A51F]
refresh=words(0x63A500,8)
refresh_exp=[0xF9401A60,0x1E2E1000,0x52800941,0x2A1F03E2,0x2A1F03E3,0x2A1F03E4,0x9404B19D,0xF9401A60]
play=words(0x766B8C,20)
play_exp=[0xA9BE57FE,0xA9014FF4,0xB9529408,0x2A0403F4,0xAA0003F3,0x7100091F,0x54000080,0xB9528668,0x7100051F,0x540000A1,0x2A1F03E2,0x52800028,0xB9129E68,0xB912867F,0xF9400268,0xAA1303E0,0xF947CD08,0xD63F0100,0xAA1303E0,0x2A1403E1]
print('r167_cleanup_caller_fingerprint','PASS' if cleanup==cleanup_exp else 'FAIL')
print('r167_native_refresh_fingerprint','PASS' if refresh==refresh_exp else 'FAIL')
print('r167_playaction_fingerprint','PASS' if play==play_exp else 'FAIL')
if cleanup!=cleanup_exp or refresh!=refresh_exp or play!=play_exp: sys.exit(1)
print('NSC_RUNTIME_R167_SOURCE_VERIFY=PASS')
