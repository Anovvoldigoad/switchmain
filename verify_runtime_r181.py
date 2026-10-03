#!/usr/bin/env python3
from pathlib import Path
import hashlib,struct,sys,re
try:
    import lz4.block
except Exception:
    lz4=None
root=Path(__file__).resolve().parent
rt=(root/'overlay/source/program/nsc_runtime_v2.cpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
core=(root/'overlay/source/program/nsc_runtime_core.cpp').read_text()
coreh=(root/'overlay/source/program/nsc_runtime_core.hpp').read_text()
rth=(root/'overlay/source/program/nsc_runtime_v2.hpp').read_text()
hdr=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
prep=(root/'prepare_exlaunch.sh').read_text()
wfs=list((root/'.github/workflows').glob('*.yml'))
wf=wfs[0].read_text() if len(wfs)==1 else ''
fn=rt[rt.index('bool InstallR181DpadFullEligibilityRollback() {'):rt.index('\n} // namespace nsc::v2',rt.index('bool InstallR181DpadFullEligibilityRollback() {'))]
case13=bridge[bridge.index('case 13: { // R181'):bridge.index('case 14:', bridge.index('case 13: { // R181'))]
checks={
 'main_thin_bootstrap': 'exl::hook::Initialize();' in main and 'nsc_runtime_initialize();' in main and 'InstallResolverHookMigrationProbe' not in main,
 'core_order': core.index('InstallResolverHookMigrationProbe();') < core.index('InstallOriginalMainRuntimePatches()') < core.index('InstallR181DpadFullEligibilityRollback()') < core.index('InstallP128AStaticPreciseGateCaveProof();') < core.index('InstallR172UjMissAnmDirectParity();') < core.index('InstallR175DpadLookupMatrixTrace();') < core.index('InstallR176ActionRegistryMatrixTrace();') < core.index('InstallR177ActionDescriptorMatrixTrace();') < core.index('InstallV2NStageRegistryProof();'),
 'runtime_c_abi':'extern \"C\" bool nsc_runtime_initialize();' in coreh and 'extern \"C\" bool nsc_runtime_initialize()' in core,
 'r181_fail_closed_core':'if (!nsc::v2::InstallR181DpadFullEligibilityRollback()) return false;' in core,
 'r181_declared':'bool InstallR181DpadFullEligibilityRollback();' in rth,
 'old_eligibility_installers_absent': all(x not in main+core+rth for x in ('InstallR178DpadAnimationEligibilityParity','InstallR179DpadAnimationEligibilityParity','InstallR180DpadNativeGateRollback')),
 'r181_ready':'[NSC:R181] READY full_rollback=1 native_gate_original=1' in rt,
 'r181_shadow_marker':'[NSC:R181] OP13_SHADOW actor=%p side=%u char=%u p2=%d' in bridge and 'no_state_write=1' in case13,
 'r181_opcode13_zero_write': all(x not in case13 for x in ('*dpad_enable = p2','pb + 0xF20) =','pb + 0xF30) =','memcpy','Write<')) and 'f30_observed' in case13 and 'f20_observed' in case13,
 'r181_gate_resolved':'ResolveExactUnique' in fn and 'kNativeGateSig' in fn and 'gate_source=resolver' in fn,
 'r181_native_gate_words':'0xB94E5768u' in fn and '0x7101F11Fu' in fn,
 'r181_zero_gate_write':'RandomAccessPatcher' not in fn and 'patcher.Write' not in fn and 'gate_patch_words=0' in fn,
 'r181_retired_eligibility':'r179_gate_patch_retired=1' in fn and 'r178_f20_mapping_retired=1' in fn and 'r180_f30_writer_retired=1' in fn and 'writer13_mutation=0' in fn,
 'r181_no_action_mutation':all(x in fn for x in ('opcode23_change=0','registry_change=0','descriptor_clone=0','action_force=0','no_char281_branch=1')),
 'r171_not_installed':'InstallR171Uj707Flag70Release();' not in core and 'ActionGateFlagReleaseHook::InstallAtOffset' not in bridge,
 'r172_installed':'InstallR172UjMissAnmDirectParity();' in core and 'bool InstallR172UjMissAnmDirectParity();' in hdr,
 'r172_resolver_driven':'GetResolvedOffset(nsc::v2::Anchor::CentralSetter, setter_off)' in bridge and 'R172_SET_ANM_DIRECT_RESOLVED' in bridge,
 'r172_guard':all(x in bridge for x in ('param2 == 0','side == 0u','semantic && member','anm1268_before == 707u','state1268_after_pre == 707u','param3 == 8')),
 'r172_other_op23_unchanged':'[NSC:V2H] OP23_SAFE_SUPPRESS' in bridge and 'setanmdirect_deferred_non_uj=1' in bridge,
 'r175_retained':'[NSC:R175] READY dpad_lookup_matrix_trace=1' in bridge,
 'r176_retained':'[NSC:R176] READY dpad_action_registry_matrix=1' in bridge,
 'r177_retained':'[NSC:R177] READY dpad_action_descriptor_matrix=1' in bridge,
 'selector_table_retained':all(x in bridge for x in ('case 0u: base_candidate = 923u','case 1u: base_candidate = 924u','case 2u: base_candidate = 921u','case 3u: base_candidate = 922u')),
 'no_char281_runtime_guard':'char_id == 281' not in bridge,
 'stage_trace_hooks_omitted':'InstallV2MStageSafeTraceHooks();' not in core,
 'voice_probes_not_installed':'InstallR165Event150VoiceReadOnlyProbe();' not in core and 'InstallR166SoundDispatchReadOnlyProbe();' not in core,
 'p128_retained':'[NSC:P128A] READY' in bridge and 'no_force708=1' in bridge and 'no_force710=1' in bridge,
 'thirty_word_plan':'WordPatch plan[30]' in rt and 'condition_words=5 p67_words=1 p128_words=24' in rt,
 'validate_before_write':rt.index('Validate ALL original words before the first write') < rt.index('patcher.Write<std::uint32_t>'),
 'workflow_runtime_core':len(wfs)==1 and 'NSC2Switch-RUNTIME-CORE-R181' in wf and 'verify_runtime_r181.py' in wf,
 'workflow_no_main_payload':'cp original/atmosphere/contents/0100FA10190A0000/exefs/main' not in wf and 'Assert no main override is shipped' in wf,
 'workflow_bootstrap_only':'cp \"$SUBSDK\" \"$EXE/subsdk9\"' in wf,
 'generic_modpack_path':'sim:data/moddingapi/NSC2Switch_ModPack.cpk' in bridge and 'sim:data/moddingapi/Tobi_Switch.cpk' in bridge,
 'prepare_r181_elf':'runtime_r181.elf' in prep,
}
for k,v in checks.items(): print(k,'PASS' if v else 'FAIL')
if not all(checks.values()): sys.exit(1)

def decode_nso(path):
    b=path.read_bytes()
    if b[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',b,o)[0]
    flags=u(0x0c); secs=[]
    for bit,foff,moff,usize,cszoff in [(0,0x10,0x14,0x18,0x60),(1,0x20,0x24,0x28,0x64),(2,0x30,0x34,0x38,0x68)]:
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
if sha(orig)!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9': print('original_main_sha256 FAIL');sys.exit(1)
print('original_main_sha256 PASS')
if sha(ref)!='904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff': print('reference_p128_sha256 FAIL');sys.exit(1)
print('reference_p128_sha256 PASS')
secs_o=decode_nso(orig); secs_r=decode_nso(ref); text_o=secs_o[0][1]; text_r=secs_r[0][1]
diff={off:(struct.unpack_from('<I',text_o,off)[0],struct.unpack_from('<I',text_r,off)[0]) for off in range(0,len(text_o)-3,4) if struct.unpack_from('<I',text_o,off)[0]!=struct.unpack_from('<I',text_r,off)[0]}
if len(diff)!=30: print('reference_delta_30_words FAIL',len(diff));sys.exit(1)
print('reference_delta_30_words PASS',len(diff))
def words(off,n):return [struct.unpack_from('<I',text_o,off+4*i)[0] for i in range(n)]
if words(0x59CEB4,2)!=[0xB94E5768,0x7101F11F]: print('r181_native_gate_fingerprint FAIL',words(0x59CEB4,2));sys.exit(1)
print('r181_native_gate_fingerprint PASS')
setter=[0xD10303FF,0x6D0523E9,0xA9067BFD,0xA9076FFC,0xA90867FA,0xA9095FF8,0xA90A57F6,0xA90B4FF4,0xF9410C08,0x4EA01C08,0x2A0303F4,0x2A0203F6,0xAA0003F3,0x2A0103F5]
if words(0x766320,len(setter))!=setter: print('r172_setter_fingerprint FAIL');sys.exit(1)
print('r172_setter_fingerprint PASS')
fallback=[0xAA1303E0,0x2A1403E1,0x52800022,0x9404886C,0x1E2E1000,0xF100001F,0x52807328,0x1A940101,0x12800002,0xAA1303E0,0x2A1F03E3,0x2A1F03E4,0x94047FA5]
if words(0x646CC8,len(fallback))!=fallback: print('r175_native_fallback_fingerprint FAIL');sys.exit(1)
print('r175_native_fallback_fingerprint PASS')
lookup=[0xA9BE57FE,0xA9014FF4,0xB94E5408,0x2A0203F5,0x2A0103F3,0xAA0003F4]
if words(0x768E84,len(lookup))!=lookup: print('r175_action_lookup_fingerprint FAIL');sys.exit(1)
print('r175_action_lookup_fingerprint PASS')
ro_base,ro=secs_o[1]; table=struct.unpack_from('<4I',ro,0x1B29960-ro_base)
if table!=(923,924,921,922): print('r175_candidate_table FAIL',table);sys.exit(1)
print('r175_candidate_table PASS',table)
reg=[0xF8408C09,0xB40001A9,0xAA0003E8,0xB940212A,0x6B01015F,0x1A9F27EA,0x9A893108,0xF86A5929]
if words(0x8364F8,8)!=reg: print('stage_registry_fingerprint FAIL');sys.exit(1)
print('stage_registry_fingerprint PASS')
print('NSC_RUNTIME_R181_SOURCE_VERIFY=PASS')
