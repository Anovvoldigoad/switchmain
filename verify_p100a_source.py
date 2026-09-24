from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parent
cpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(ROOT/'overlay/source/program/main.cpp').read_text()
block=cpp.split('// P100A — native action710 corridor landmark trace.',1)[1]
checks={
'entrypoint':'nsc::InstallP100AAction710CorridorLandmarks();' in main,
'decl':'void InstallP100AAction710CorridorLandmarks();' in hpp,
'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
'p99_not_installed':'InstallP99ACleanupGate1278Trace();' not in main,
'ready':'[NSC:P100A] READY' in block,
'landmark':'[NSC:P100A] LANDMARK' in block,
'five_inline':sum(block.count(x) for x in ['P100AEntryLandmarkHook','P100AZeroPathLandmarkHook','P100AC48ReturnLandmarkHook','P100ALookupLandmarkHook','P100ARequest710LandmarkHook'])>=10,
'offsets':all(x in block for x in ['0x7E6A58','0x7E6BB4','0x7E6B08','0x7E6C34','0x7E6EA8']),
'fingerprints':all(x in block for x in ['0xAA1703FA','0xB94E5668','0xAA1803F6','0xB4001380','0x528058C1']),
'no_blr_replay':'no_blr_replay=1' in block and 'd63f0100' not in block.lower(),
'no_force710':'no_force710=1' in block,
'no_force708':'no_force708=1' in block,
'no_action_rewrite':'no_action_rewrite=1' in block,
'no_char281_branch':not re.search(r'char(?:_id)?\s*==\s*281|cid\s*==\s*281',block),
'helper_order':cpp.find('bool MatchWords(')<cpp.find('InstallP100ALandmarksInternal()') and cpp.find('void LogFingerprintFail(')<cpp.find('InstallP100ALandmarksInternal()'),
}
for k,v in checks.items(): print(k,'PASS' if v else 'FAIL'); assert v,k
for rel,exp in [
('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),
('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]:
 got=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(); print(rel,got); assert got==exp
push=[]
for p in sorted((ROOT/'.github/workflows').glob('*.yml')):
 t=p.read_text()
 if re.search(r'(?m)^  push:\s*$',t): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p100a.yml']
wf=(ROOT/'.github/workflows/build-subsdk9-p100a.yml').read_text()
assert 'git -C exlaunch checkout --detach 229bbd6' in wf
assert '[NSC:P100A] LANDMARK' in wf
assert 'nsc::InstallP100AAction710CorridorLandmarks();' in wf
assert 'NSC-P100A-action710-corridor-landmarks' in wf
assert 'GATE1278' not in wf
print('P100A_DROPIN_SOURCE_VERIFY=PASS')
