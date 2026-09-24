from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parent
cpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(ROOT/'overlay/source/program/main.cpp').read_text()
block=cpp.split('HOOK_DEFINE_TRAMPOLINE(P99AGate1278TraceHook)',1)[1].split('static bool InstallP99AGate1278Internal()',1)[0]
installer=cpp.split('void InstallP99ACleanupGate1278Trace()',1)[1]
checks={
'entrypoint':'nsc::InstallP99ACleanupGate1278Trace();' in main,
'decl':'void InstallP99ACleanupGate1278Trace();' in hpp,
'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in installer,
'p97_p98_not_installed':'InstallP97' not in main and 'InstallP98B' not in main,
'ready':'[NSC:P99A] READY' in cpp,
'gate_log':'[NSC:P99A] GATE1278' in cpp,
'topology_log':'[NSC:P99A] TOPO' in cpp,
'offset':'kP99AGate1278Offset = 0x7EB518' in cpp,
'vslot':'kP99AGate1278Slot = 0x1278' in cpp,
'fingerprint':all(x in cpp for x in ['0xA9BE57FE','0xA9014FF4','0xB94F2408','0x7100051F','0x54000120','0xAA0003F3','0x97FD9310','0x350000C0']),
'one_p99_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P99A')==1,
'orig_once':block.count('Orig(')==1,
'corridor_focus':all(x in block for x in ['pre.action == 707u','pre.action == 708u','pre.action == 710u']),
'raw_dependencies':all(x in block for x in ['0xF24','0x106F4','0x10F54','0x10F58','0x10F60','0x10F64','kP99AVslot1008']),
'provenance':all(x in block for x in ['caller_off=0x%lx','slot1278_off=0x%lx','slot1008_off=0x%lx']),
'ret_logged':'semantic=%u ret=%u' in block,
'no_state_write':'no_state_write=1' in installer and 'no_e94_write=1' in installer and 'no_e9c_write=1' in installer,
'no_force710':'no_force710=1' in installer,
'no_force708':'no_force708=1' in installer,
'no_char281_branch':not re.search(r'char(?:_id)?\s*==\s*281|cid\s*==\s*281',block),
'helper_order':cpp.find('bool MatchWords(')<cpp.find('InstallP99AGate1278Internal()') and cpp.find('void LogFingerprintFail(')<cpp.find('InstallP99AGate1278Internal()'),
}
for k,v in checks.items():
 print(k,'PASS' if v else 'FAIL'); assert v,k
pairs=[
('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),
('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]
for rel,exp in pairs:
 got=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(); print(rel,got); assert got==exp
push=[]
for p in sorted((ROOT/'.github/workflows').glob('*.yml')):
 t=p.read_text()
 if re.search(r'(?m)^  push:\s*$',t): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p99a.yml']
wf=(ROOT/'.github/workflows/build-subsdk9-p99a.yml').read_text()
assert 'git -C exlaunch checkout --detach 229bbd6' in wf
assert 'NSC-P99A-cleanup-gate1278-trace' in wf
print('P99A_DROPIN_SOURCE_VERIFY=PASS')
