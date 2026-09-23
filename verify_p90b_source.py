from pathlib import Path
import hashlib, sys
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
checks={
 'entrypoint':'nsc::InstallP90BZeroExtraHandoffTrace();' in main,
 'decl':'void InstallP90BZeroExtraHandoffTrace();' in hpp,
 'p89_parent':'InstallP89APhase3ActorPredBridge();' in cpp,
 'ready':'[NSC:P90B] READY' in cpp,
 'handoff':'[NSC:P90B] HANDOFF' in cpp,
 'ea4':'pre_ea4' in cpp and 'post_ea4' in cpp,
 'bda4':'pre_bda4' in cpp and 'post_bda4' in cpp,
 'bdc8':'pre_bdc8' in cpp and 'post_bdc8' in cpp,
 'zero_extra':'zero_extra_trampolines=1' in cpp,
 'no_p90_new_hook':'P90ActionLookupHook' not in cpp and 'P90ActionGateHook' not in cpp,
 'no_char281':'cid == 281' not in cpp and 'cid==281' not in cpp,
 'no_force708':'index = 708' not in cpp and 'index=708' not in cpp,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
for rel,want in [
 ('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),
 ('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]:
 p=root/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); print(rel,got); assert got==want
# Only P90B may have push trigger. Parse text simply to avoid PyYAML dependency in CI.
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 t=p.read_text()
 if '\n  push:' in t or '\npush:' in t: push.append(p.name)
print('push_enabled_workflows',push)
assert push==['build-subsdk9-p90b.yml']
print('P90B_DROPIN_SOURCE_VERIFY=PASS')
