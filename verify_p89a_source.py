from pathlib import Path
import hashlib, sys
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
ids=(root/'overlay/source/program/p81_ougi_awake_ids.hpp').read_text()
checks={
 'entrypoint': 'nsc::InstallP89APhase3ActorPredBridge();' in main,
 'decl': 'void InstallP89APhase3ActorPredBridge();' in hpp,
 'hook_offset': 'kP89ActorPred = 0x7E24EC' in cpp,
 'namespace_fix': 'p81_data::ContainsOugiAwakeningId(cid)' in cpp,
 'semantic_gate': 'P64QuerySemanticUltimateJutsu(actor)' in cpp,
 'phase3': 'bda4 == 3' in cpp and 'bdc8 == 1' in cpp,
 'preserve_native': 'const uint32_t out = bridge ? 1u : native_ret;' in cpp,
 'ready_marker': '[NSC:P89A] READY' in cpp,
 'pred_marker': '[NSC:P89A] ACTOR_PRED' in cpp,
 'correct_106f4': 's106f4' in cpp and 'b+0x106F4' in cpp,
 'correct_123e0': 's123e0' in cpp and 'b+0x123E0' in cpp,
 'correct_123e4': 's123e4' in cpp and 'b+0x123E4' in cpp,
 'no_bad_116f4': 's116f4' not in cpp,
 'no_bad_133e0': 's133e0' not in cpp,
 'no_bad_133e4': 's133e4' not in cpp,
 'generated_membership': 'ContainsOugiAwakeningId' in ids,
 'no_char281_branch': 'cid == 281' not in cpp and 'cid==281' not in cpp,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
for rel,want in [
 ('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),
 ('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]:
 p=root/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); print(rel,got); assert got==want
print('P89A_DROPIN_SOURCE_VERIFY=PASS')
