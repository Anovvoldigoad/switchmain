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
wf=(root/'.github/workflows/build-runtime-v2l.yml').read_text()
sfx=(root/'overlay/source/program/nsc_sfx_list_generated.hpp').read_text()

checks={
 'main_order': main.index('InstallResolverHookMigrationProbe();') < main.index('InstallOriginalMainRuntimePatches()') < main.index('InstallP128AStaticPreciseGateCaveProof();'),
 'fail_closed_main': 'if (!nsc::v2::InstallOriginalMainRuntimePatches()) return;' in main,
 'random_access_patcher': '#include <lib/patch/random_access_patcher.hpp>' in rt and 'exl::patch::RandomAccessPatcher patcher;' in rt,
 'validate_before_write': rt.index('Validate ALL original words before the first write') < rt.index('patcher.Write<std::uint32_t>'),
 'thirty_word_plan': 'WordPatch plan[30]' in rt and 'condition_words=5 p67_words=1 p128_words=24' in rt,
 'paired_file_disabled': 'paired_main_file=0' in rt,
 'runtime_gate_accessor': 'GetDerivedUjGateLoadOffset' in h and 'GetDerivedUjGateLoadOffset' in bridge,
 'gate_hook_dynamic': 'HOOK name=UJ_GATE_LOAD source=resolver_derived' in bridge and 'P124GateHook::InstallAtOffset(off)' in bridge,
 'uj_post_dynamic': 'HOOK name=UJ_SESSION_POST source=resolver_derived' in bridge,
 'six_core_dynamic': all(x in bridge for x in (
    'HOOK name=EVENT236 source=resolver','HOOK name=PLAY_ACTION source=resolver',
    'HOOK name=CENTRAL_SETTER source=resolver','HOOK name=CPK_BIND source=resolver',
    'HOOK name=CHARACODE_GETTER source=resolver')),
 'v2d_arch_markers': '[NSC:V2D] RESOLVER_READY' in rt and '[NSC:V2D] RUNTIME_PATCH_READY' in rt,
 'original_main_readme': '2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9' in (root/'README_RUNTIME_V2L.md').read_text(),
 'workflow_only_v2l': len(list((root/'.github/workflows').glob('*.yml')))==1 and 'NSC-RUNTIME-V2L-stage-resource-environment-trace' in wf,
 'workflow_original_main': 'original/atmosphere/contents/0100FA10190A0000/exefs/main' in wf,
 'workflow_not_reference_main': 'reference_p128/atmosphere/contents/0100FA10190A0000/exefs/main" "$OUT/atmosphere' not in wf,
 'prepare_copies_sfx_header': 'nsc_sfx_list_generated.hpp' in prep,
 'logger_include_order': rt.index('#include "lib.hpp"') < rt.index('#include <program/loggers.hpp>'),
 'no_char281_runtime': 'char_id == 281' not in bridge and 'char==281' not in bridge and 'char = 281' not in bridge,
 'dpad17_base': 'constexpr ptrdiff_t kDpadChargeBaseOffset = 0x12B78;' in bridge,
 'dpad17_source_parity_handler': 'HandleDpadChargeSourceParity' in bridge and '[NSC:V2E] DPAD17_APPLY' in bridge,
 'dpad17_arrow4': 'case 4: base[3] = charge; break;' in bridge,
 'dpad17_no_abs16_cap': 'IsFiniteAbsLe16(charge)' not in bridge and 'fabs' not in bridge[bridge.index('HandleDpadChargeSourceParity'):bridge.index('uint32_t HandleStageMove')],
 'opcode12_unchanged_shadow': 'VIS_SHADOW' in bridge,
 'opcode23_present': 'case 23: // source me_play_action' in bridge,
 'v2i_op23_safe_marker': '[NSC:V2I] OP23_SAFE_SUPPRESS' in bridge and 'full_animation_suppressed=1' in bridge,
 'v2i_op23_no_766320_call': 'call_766320=0' in bridge,
 'v2i_op23_no_playaction': 'playaction_wrapper=0' in bridge,
'v2i_activation_core_ab': '[NSC:V2I] IZANAGI_CORE_AB' in bridge and 'V2IApplyIzanagiActivationCoreAB' in bridge,
 'v2i_activation_exact_fixture': 'action_param != 77' in bridge and 'std::strcmp(text, "SPTYPE_ACTION10")' in bridge and 'constexpr const char* kCond = "SW_MTOB_XH";' in bridge,
 'v2i_activation_no_global_damage_hack': 'force_no_damage' not in bridge.lower() and 'no_damage = true' not in bridge.lower(),
 'v2h_stage_enter_retained': '[NSC:V2H] STAGE2_ENTER' in bridge,
 'v2h_stage_fail_retained': '[NSC:V2H] STAGE2_FAIL' in bridge,
 'v2i_stage_parity': '[NSC:V2I] STAGE2_PARITY' in bridge and 'fix_actor=1 fix_enemy=%u poststage=0 pc_source_parity=1' in bridge,
 'v2i_stage_enemy_fix': 'reinterpret_cast<ActorFn>(base + kFixCharPositionOffset)(enemy);' in bridge,
 'v2i_stage_no_poststage_call': 'reinterpret_cast<VoidFn>(base + kPostStageOffset)();' not in bridge[bridge.index('uint32_t HandleStageMove'):bridge.index('uint32_t HandleActionAnimation')],
 'v2i_op26_case': 'case 26: { // source me_play_voice_string' in bridge,
 'v2i_op26_play': '[NSC:V2I] OP26_PLAY' in bridge and 'native_813d88_contract=1' in bridge,
 'v2i_op26_source_index': 'nsc_sfx_list_generated::FindIndex(text)' in bridge and 'sfx_index + 0x7000' in bridge,
 'v2i_op26_slot1030': 'vtable[0x1030 / sizeof(void*)]' in bridge and 'reinterpret_cast<SoundFn>(slot1030)(target, sound_command, 0)' in bridge,
 'sfx_count_160': 'kCount = 160' in sfx,
 'sfx_etc_l': '"S_PL_etc_l"' in sfx,
 'sfx_etc_m': '"S_PL_etc_m"' in sfx,
 'sfx_dmg_common': '"S_PL_DMG_cmn_vS_rv"' in sfx,
 'p57_float_abi_preserved': 'int32_t a3, float rate)' in bridge and 'Orig(actor, action, a2, a3, rate);' in bridge,
 'v2g_direct_marker_removed': '[NSC:V2G] OP23_DIRECT_ANM' not in bridge,
 'v2f_marker_removed': '[NSC:V2F] OP23_NO_PLAYACTION_AB' not in bridge,
 'no_guessed_setanmdirect_offset': 'kSetAnmDirectOffset' not in bridge,
 'v2k_ready': '[NSC:V2K] READY recovery_baseline=V2I' in bridge and 'InstallV2KRecoveryPassiveProbe();' in main,
 'v2k_passive_snapshot': '[NSC:V2K] DPAD_PASSIVE_SNAPSHOT' in bridge and 'extra_gameplay_write=0' in bridge and 'v2j_inline_hook=0' in bridge,
 'v2k_stage_safe': '[NSC:V2K] STAGE_SAFE_BASELINE' in bridge and 'v2j_poststage_removed=1 poststage=0 extra_stage_call=0' in bridge,
 'v2k_no_v2j_inline_hook': 'InstallV2JDpadNativeConsumerProbe' not in main and 'DPAD_NATIVE_CONSUMER' not in bridge and 'DPAD_NATIVE_READY' not in bridge,
 'v2k_no_poststage_call': 'reinterpret_cast<VoidFn>(base + kPostStageOffset)();' not in bridge[bridge.index('uint32_t HandleStageMove'):bridge.index('uint32_t HandleActionAnimation')],
 'v2k_audio_frozen': '[NSC:V2I] OP26_PLAY' in bridge and 'slot1030' in bridge,
 'v2l_main_call': 'InstallV2LStageOnlyTraceHooks();' in main,
 'v2l_stage_ready': '[NSC:V2L] READY stage_only=1 installed=1' in bridge,
 'v2l_stage_graph': '[NSC:V2L] STAGE_GRAPH' in bridge and 'readonly=1' in bridge,
 'v2l_stage_trace_window': '[NSC:V2L] STAGE_TRACE_ARM' in bridge and '[NSC:V2L] STAGE_TRACE_DISARM' in bridge,
 'v2l_request_trace': 'FileLoadRequestHook::InstallAtOffset(kFileLoadRequestOffset);' in bridge,
 'v2l_file_open_trace': 'FileOpenHook::InstallAtOffset(kFileOpenOffset);' in bridge,
 'v2l_stage_handle_observe': 'StageHandleHook::InstallAtOffset(kHandleStageChangeOffset);' in bridge,
 'v2l_poststage_observe_only': 'PostStageHook::InstallAtOffset(kPostStageOffset);' in bridge and 'manual_poststage_call=0' in bridge,
 'v2l_no_stage_post_call': 'reinterpret_cast<VoidFn>(base + kPostStageOffset)();' not in bridge[bridge.index('uint32_t HandleStageMove'):bridge.index('uint32_t HandleActionAnimation')],
 'v2l_no_dpad_behavior_change': 'dpad_change=0' in bridge,
 'v2l_no_voice_behavior_change': 'voice_change=0' in bridge,
 'v2l_no_p128_behavior_change': 'p128_change=0' in bridge,

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
if len(diff)!=30:
    print('unexpected diff',[(hex(k),hex(v[0]),hex(v[1])) for k,v in diff.items()]);sys.exit(1)

expected={
0x747878:(0x52804009,0x528040A9),
0x7774DC:(0x7108031F,0x7108171F),
0x777770:(0x7108027F,0x7108167F),
0x777938:(0x7108027F,0x7108167F),
0x777A6C:(0x7108027F,0x7108167F),
0x7F2A9C:(0xBD001FE0,0xD503201F),
0x77C480:(0x54000B81,0x1400000E),
0x77C494:(0x34000AC0,0xD503201F),
0x77C4A8:(0x34000A20,0xD503201F),
0x77C4B4:(0x34000300,0x14000018),
0x77C4B8:(0xF0009619,0x7100291F),0x77C4BC:(0x913C2339,0x54000220),
0x77C4C0:(0xAA1903E0,0x71002D1F),0x77C4C4:(0x942A6437,0x540001E0),
0x77C4C8:(0xF9400268,0x71003D1F),0x77C4CC:(0xAA1303E0,0x54000181),
0x77C4D0:(0xF9402508,0xB94E56EA),0x77C4D4:(0xD63F0100,0x7104615F),
0x77C4D8:(0x11000401,0x54000129),0x77C4DC:(0xB0009680,0x7140055F),
0x77C4E0:(0x91292C00,0x540000E2),0x77C4E4:(0x942A642F,0xF9410EEA),
0x77C4E8:(0xF94002E8,0xB40000AA),0x77C4EC:(0xAA1703E0,0xB9402D4A),
0x77C4F0:(0xF9402508,0x710B0D5F),0x77C4F4:(0xD63F0100,0x54000041),
0x77C4F8:(0x11000401,0x14000002),0x77C4FC:(0xB0009940,0x1400003D),
0x77C500:(0x91086800,0x17FFFFE1),
0x77C520:(0xB40003E0,0x1400001F),
}
if diff!=expected:
    print('diff map mismatch')
    for k in sorted(set(diff)|set(expected)):
        if diff.get(k)!=expected.get(k): print(hex(k),diff.get(k),expected.get(k))
    sys.exit(1)
print('reference_delta_exact_30_words PASS')

# Offline resolver signatures still unique in ORIGINAL main.
def parse_arr(name):
    m=re.search(rf'{re.escape(name)}\[\]\s*=\s*\{{([^}}]+)\}};',rt,re.S)
    if not m: raise RuntimeError('missing '+name)
    return [int(x,16) for x in re.findall(r'0x[0-9A-Fa-f]+',m.group(1))]
def scan(text,vals,masks):
    out=[]
    limit=len(text)-4*len(vals)+1
    # Almost every resolver pattern begins with a fully fixed AArch64 word.
    # Use that as an indexed byte needle instead of rescanning ~5M words per
    # pattern; fall back to aligned scanning only for masked first words.
    if masks[0] == 0xFFFFFFFF:
        needle=struct.pack('<I',vals[0])
        pos=text.find(needle)
        while pos != -1:
            if pos % 4 == 0 and pos < limit:
                if all((struct.unpack_from('<I',text,pos+4*i)[0]&m)==(v&m) for i,(v,m) in enumerate(zip(vals,masks))):
                    out.append(pos)
            pos=text.find(needle,pos+1)
        return out
    for off in range(0,limit,4):
        w=struct.unpack_from('<I',text,off)[0]
        if (w&masks[0]) != (vals[0]&masks[0]):
            continue
        if all((struct.unpack_from('<I',text,off+4*i)[0]&m)==(v&m) for i,(v,m) in enumerate(zip(vals,masks))):
            out.append(off)
    return out
specs=[
 ('CHARACODE_GETTER','kCharVal','kCharMask',0x3F4150),('CPK_BIND','kCpkVal','kCpkMask',0x473190),
 ('EVENT236','kEvent236Val','kEvent236Mask',0x816300),('PLAY_ACTION','kPlayVal','kPlayMask',0x766B8C),
 ('CENTRAL_SETTER','kSetterVal','kSetterMask',0x766320),('UJ_SESSION_OUTER','kOuterVal','kOuterMask',0x7EF098),
 ('STATE137_CONTROLLER','kState137Val','kState137Mask',0x7E6EA8)]
for name,vn,mn,exp in specs:
    hits=scan(o,parse_arr(vn),parse_arr(mn)); ok=hits==[exp]
    print('offline_original_'+name,'PASS' if ok else 'FAIL','hits='+','.join(hex(x) for x in hits[:4]))
    if not ok:sys.exit(1)

# Source must contain every replacement word used by the 24-word UJ patch.
for off,(before,after) in expected.items():
    if off>=0x77C480 and f'0x{after:08X}u' not in rt:
        print('missing source replacement',hex(off),hex(after));sys.exit(1)
print('source_contains_uj_runtime_delta PASS')
# V2I keeps 0x766320 out of the safe opcode23 path. V2G proved that it runs
# PL_ANM930 and its event stream but also reproduces the visual disappearance;
# lock the observed 0x1268 animation-state write as evidence, without claiming
# that the low-level animation primitive itself is semantically disproven.
def words(off,n):
    return [struct.unpack_from('<I',o,off+4*i)[0] for i in range(n)]

def expect_words(name,off,expected_words):
    got=words(off,len(expected_words)); ok=got==expected_words
    print(name,'PASS' if ok else 'FAIL','off='+hex(off))
    if not ok:
        print(' got     ',[f'{x:08X}' for x in got])
        print(' expected',[f'{x:08X}' for x in expected_words])
        sys.exit(1)

expect_words('static_766320_state_writes_rejection_evidence',0x766A50,[
 0xB9126668,0x1E380008,0xB9127268,0xF9410E68,
 0xB9126A75,0xBD126E68,0xB9127674,0xB900311F])
expect_words('static_setaction_immediate_e94_e98',0x7A8464,[
 0x52808D09,0x72A00029,0xB94E940A,0xB90E9401,0xB90E980A])

# Ensure opcode23's action-mode branch contains no 0x766320 resolver call or PlayAction.
start=bridge.index('if (action_mode) {\n        const auto* tb', bridge.index('// V2I: preserve the V2H/V2F-safe opcode23 suppression as the baseline.'))
end=bridge.index('// Opcode22 remains unchanged as a control path.',start)
op23=bridge[start:end]
for forbidden in ('CentralSetter','DirectAnmFn','kPlayActionOffset','reinterpret_cast<PlayFn>'):
    if forbidden in op23:
        print('v2i_opcode23_safe_branch FAIL forbidden='+forbidden);sys.exit(1)
print('v2i_opcode23_safe_branch PASS')

# Source SFX index sanity against the exact three generic UJ cues seen in log29.
def parse_sfx_names(text):
    return re.findall(r'^\s*"([^"]+)",\s*$', text, re.M)
names=parse_sfx_names(sfx)
if len(names)!=160:
    print('sfx_parse_count FAIL',len(names));sys.exit(1)
expected_idx={'S_PL_etc_l':21,'S_PL_etc_m':22,'S_PL_DMG_cmn_vS_rv':153}
for name,idx in expected_idx.items():
    got=names.index(name) if name in names else -1
    ok=got==idx
    print('sfx_index_'+name,'PASS' if ok else 'FAIL','index='+str(got))
    if not ok:sys.exit(1)

# Native Switch generic sound contract used by V2I opcode26.
expect_words('static_switch_sound_event_813d88',0x813D88,[
 0xF81F0FFE,0x79C04828,0x11401D01,0xF9400008,0xF9481908,
 0x2A1F03E2,0xD63F0100,0x52800020,0xF84107FE,0xD65F03C0])

# Ensure the stage handler's mutation section does not call the old extra PostStage.
stage_src=bridge[bridge.index('uint32_t HandleStageMove'):bridge.index('uint32_t HandleActionAnimation')]
if 'reinterpret_cast<VoidFn>(base + kPostStageOffset)();' in stage_src:
    print('stage_poststage_removed FAIL');sys.exit(1)
print('stage_poststage_removed PASS')

print('NSC_RUNTIME_V2L_SOURCE_VERIFY=PASS')
