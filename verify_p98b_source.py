from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parent
cpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(ROOT/'overlay/source/program/main.cpp').read_text()
checks={
'entrypoint':'nsc::InstallP98BState125ProvenanceTrace();' in main,
'decl':'void InstallP98BState125ProvenanceTrace();' in hpp,
'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in cpp.split('void InstallP98BState125ProvenanceTrace()',1)[1],
'p97_absent':'InstallP97' not in main and 'P97TransitionSelectorHook' not in cpp,
'ready':'[NSC:P98B] READY' in cpp,
'state_req_log':'[NSC:P98B] STATE_REQ' in cpp,
'offset':'kP98BStateRequestOffset = 0x7A89A4' in cpp,
'vslot':'kP98BStateRequestSlot = 0xE28' in cpp,
'fingerprint':all(x in cpp for x in ['0xA9BD5FFE','0xA90157F6','0xA9024FF4','0x2A0103F4','0xAA0003F3']),
'one_p98b_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P98B')==1,
'orig_once':cpp.split('HOOK_DEFINE_TRAMPOLINE(P98BStateRequestProvenanceHook)',1)[1].split('static bool InstallP98BStateRequestProvenanceInternal()',1)[0].count('Orig(')==1,
'req125_focus':'requested_state == 125u' in cpp,
'action708_focus':'pre.action == 708u' in cpp,
'provenance':all(x in cpp for x in ['caller_off=0x%lx','call_m8=%08x','call_m4=%08x','slot_e28_off=0x%lx']),
'states':all(x in cpp for x in ['e9c=%u->%u','ea4=%08x->%08x','bda4=%u->%u','bda8=%u->%u']),
'no_state_write':'no_state_write=1' in cpp and 'no_e9c_write=1' in cpp,
'no_force710':'no_force710=1' in cpp,
'no_force708':'no_force708=1' in cpp,
'no_char281_branch':not re.search(r'char(?:_id)?\s*==\s*281|cid\s*==\s*281',cpp),
'helper_order':cpp.find('bool MatchWords(')<cpp.find('InstallP98BStateRequestProvenanceInternal()') and cpp.find('void LogFingerprintFail(')<cpp.find('InstallP98BStateRequestProvenanceInternal()'),
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
print('push_enabled_workflows',push); assert push==['build-subsdk9-p98b.yml']
wf=(ROOT/'.github/workflows/build-subsdk9-p98b.yml').read_text()
assert 'git -C exlaunch checkout --detach 229bbd6' in wf
assert 'NSC-P98B-state125-provenance-trace' in wf
print('P98B_DROPIN_SOURCE_VERIFY=PASS')
