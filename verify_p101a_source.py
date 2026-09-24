from pathlib import Path
import hashlib,re
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P101A')
block=cpp[start:]
checks={
 'entrypoint':'nsc::InstallP101AEventDriven708EndGuard();' in main,
 'decl':'void InstallP101AEventDriven708EndGuard();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'p100c_not_installed':'InstallP100COneTrampolineAction710RouteOracle();' not in main,
 'ready':'[NSC:P101A] READY' in cpp,
 'hold125_log':'[NSC:P101A] HOLD125' in cpp,
 'pass125_log':'[NSC:P101A] PASS125' in cpp,
 'op23_log':'[NSC:P101A] OP23' in cpp and '[NSC:P101A] OP23_RESULT' in cpp,
 'state_req_offset':'kP101StateRequestOffset = 0x7A89A4' in cpp,
 'one_p101_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P101')==1,
 'no_p101_inline':'HOOK_DEFINE_INLINE(P101' not in cpp,
 'req125_gate':'requested_state == 125u' in block,
 'action708_gate':'pre.action == 708u' in block,
 'semantic_gate':'P64QuerySemanticUltimateJutsu(actor)' in block,
 'membership_gate':'p81_data::ContainsOugiAwakeningId(cid)' in block,
 'op23_latch':'kP101Op23SeenBit' in cpp and 'P101SetOp23Seen(actor, true)' in cpp and 'P101QueryOp23Seen(actor)' in block,
 'bounded_fail_open':'kP101HoldEa4Max = 0x3000u' in cpp and 'pre.ea4 <= kP101HoldEa4Max' in block,
 'guard_returns_zero':'if (hold)' in block and 'return 0u;' in block,
 'orig_fallback':'Orig(actor, requested_state, arg2, arg3)' in block,
 'fingerprint':all(x in block for x in ['0xA9BD5FFE','0xA90157F6','0xA9024FF4','0x2A0103F4','0xAA0003F3','0x34000282','0xF9400268','0xAA1303E0']),
 'victim_shadow_preserved':'case 12:' in cpp and 'VIS_SHADOW' in cpp and 'case 14:' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|requested_state\s*=\s*710|return\s+710',block),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|requested_state\s*=\s*708|return\s+708',block),
 'no_action_write':not re.search(r'\+\s*0x1268\)\s*=(?!=)|\.action\s*=(?!=)',block),
 'no_e94_write':not re.search(r'\+\s*0xE94\)\s*=',block,re.I),
 'no_bda4_write':not re.search(r'\+\s*0xBDA4\)\s*=',block,re.I),
 'no_char281_branch':not re.search(r'(?:char_id|cid)\s*==\s*281|281\s*==\s*(?:char_id|cid)',block),
 'helper_order':cpp.find('bool MatchWords(')<cpp.find('InstallP101State125GuardInternal()') and cpp.find('void LogFingerprintFail(')<cpp.find('InstallP101State125GuardInternal()'),
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
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p101a.yml']
print('P101A_DROPIN_SOURCE_VERIFY=PASS')
