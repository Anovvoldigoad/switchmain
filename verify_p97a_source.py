from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parent
cpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(ROOT/'overlay/source/program/main.cpp').read_text()
checks={
'entrypoint':'nsc::InstallP97AEarlyTransitionGuard();' in main,
'decl':'void InstallP97AEarlyTransitionGuard();' in hpp,
'parent_p89':'InstallP89APhase3ActorPredBridge();' in cpp.split('void InstallP97AEarlyTransitionGuard()',1)[1],
'ready':'[NSC:P97A] READY' in cpp,
'guard_log':'[NSC:P97A] GUARD' in cpp,
'one_new_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P97')==1 and 'HOOK_DEFINE_TRAMPOLINE(P97EarlyTransitionGuardHook)' in cpp,
'no_p97_inline':'HOOK_DEFINE_INLINE(P97' not in cpp,
'selector_offset':'kP97TransitionSelectorOffset = 0x7EFEBC' in cpp,
'fingerprint':all(x in cpp for x in ['0xA9BD5FFE','0xA90157F6','0xA9024FF4','0x2A0103F4','0x97FDDAF2']),
'compile_order_helpers': cpp.index('template <size_t N>\nbool MatchWords(ptrdiff_t offset, const uint32_t (&expected)[N]);') < cpp.index('static bool InstallP97Internal()') and cpp.index('void LogFingerprintFail(const char* name, ptrdiff_t offset);') < cpp.index('static bool InstallP97Internal()'),
'semantic_gate':'P64QuerySemanticUltimateJutsu(actor)' in cpp,
'membership_gate':'p81_data::ContainsOugiAwakeningId(cid)' in cpp,
'keyed707_gate':'P97Descriptor707HasKey' in cpp and 'd + 0x94' in cpp,
'pre_handoff_gate':all(x in cpp for x in ['action == 707u','e94 == 136u','e9c == 0u','bda4 == 1u','bda8 == 0u','bdc8 == 0u']),
'native_no_transition':'if (guard) return 0u;' in cpp,
'orig_preserved':'return Orig(actor, context_code);' in cpp,
'mute_p95_scan':'g_p96_descriptor_trace_mode || g_p97_transition_guard_mode' in cpp and 'g_p97_transition_guard_mode = true;' in cpp,
'no_force710':'no_force710=1' in cpp,
'no_force708':'no_force708=1' in cpp,
'no_action_rewrite':'no_action_rewrite=1' in cpp,
'no_char281_branch':not re.search(r'char(?:_id)?\s*==\s*281|cid\s*==\s*281',cpp),
}
for k,v in checks.items(): print(k,'PASS' if v else 'FAIL'); assert v,k
pairs=[
('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),
('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]
for rel,exp in pairs:
 got=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(); print(rel,got); assert got==exp
push=[]
for p in sorted((ROOT/'.github/workflows').glob('*.yml')):
 t=p.read_text()
 if re.search(r'(?m)^  push:\s*$',t): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p97a.yml']
wf=(ROOT/'.github/workflows/build-subsdk9-p97a.yml').read_text()
assert 'git -C exlaunch checkout --detach 229bbd6' in wf
assert 'NSC-P97A-v2-early-transition-guard' in wf
print('P97A_DROPIN_SOURCE_VERIFY=PASS')
