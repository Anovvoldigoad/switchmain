from pathlib import Path
import hashlib,re
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
checks={
 'entrypoint':'nsc::InstallP100COneTrampolineAction710RouteOracle();' in main,
 'decl':'void InstallP100COneTrampolineAction710RouteOracle();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in cpp[cpp.find('void InstallP100COneTrampolineAction710RouteOracle()'):],
 'p100b_not_installed':'InstallP100BOneShotAction710RouteSweep();' not in main,
 'ready':'[NSC:P100C] READY' in cpp,
 'oracle_log':'[NSC:P100C] ORACLE' in cpp,
 'helper_offset':'kP100CHelperOffset = 0x64942C' in cpp,
 'five_route_sites':all(x in cpp for x in ['0x7E6AB4','0x7E6ACC','0x7E6AE4','0x7E6B20','0x7E6D68']),
 'route13':'caller_off == 0x7E6B20 && ret == 0x13u' in cpp,
 'one_p100c_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P100C')==1,
 'no_p100c_inline':'HOOK_DEFINE_INLINE(P100C' not in cpp,
 'orig_once':cpp[cpp.find('HOOK_DEFINE_TRAMPOLINE(P100C'):cpp.find('static bool InstallP100CRouteOracleInternal')].count('Orig(')==1,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710',cpp[cpp.find('// P100C'):]),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708',cpp[cpp.find('// P100C'):]),
 'no_char281_branch':not re.search(r'(?:char_id|cid)\s*==\s*281|281\s*==\s*(?:char_id|cid)',cpp[cpp.find('// P100C'):]),
 'fingerprint':all(x in cpp for x in ['0xA9BC67FE','0xA9015FF8','0xA90257F6','0xA9034FF4','0xD000D7D8','0xF9426318','0xF9400315','0xB40024F5']),
 'helper_order':cpp.find('bool MatchWords(')<cpp.find('InstallP100CRouteOracleInternal()') and cpp.find('void LogFingerprintFail(')<cpp.find('InstallP100CRouteOracleInternal()'),
}
for k,v in checks.items():
 print(k,'PASS' if v else 'FAIL')
 assert v,k

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired='paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore='restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 # push must be an actual top-level trigger line under on, not merely text in shell commands
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p100c.yml']
print('P100C_DROPIN_SOURCE_VERIFY=PASS')
