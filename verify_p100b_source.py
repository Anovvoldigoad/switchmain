from pathlib import Path
import hashlib,re
ROOT=Path(__file__).resolve().parent
cpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(ROOT/'overlay/source/program/main.cpp').read_text()
block=cpp.split('// P100B — one-shot native action710 route sweep.',1)[1]
checks={
'entrypoint':'nsc::InstallP100BOneShotAction710RouteSweep();' in main,
'decl':'void InstallP100BOneShotAction710RouteSweep();' in hpp,
'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
'old_not_installed':all(x not in main for x in ['InstallP97','InstallP98B','InstallP99A','InstallP100A']),
'ready':'[NSC:P100B] READY' in block,
'route_log':'[NSC:P100B] ROUTE' in block,
'one_shot':'one_shot_trace=1' in block,
'inline_count':block.count('HOOK_DEFINE_INLINE(P100B')>=16,
'offsets':all(x in block for x in ['0x488B24','0x7E6500','0x7E6520','0x7E664C','0x7E6768','0x7E6814','0x7E6880','0x7E6A58','0x7E6B08','0x7E6B10','0x7E6BB4','0x7E6C34','0x7E6C50','0x7E6D0C','0x7E6D58','0x7E6EA8']),
'no_trampoline':'HOOK_DEFINE_TRAMPOLINE(P100B' not in block and 'zero_extra_trampolines=1' in block,
'no_blr_replay':'no_blr_replay=1' in block,
'no_cmp_replay':'no_cmp_replay=1' in block,
'no_branch_rewrite':'no_branch_rewrite=1' in block,
'no_state_write':'no_state_write=1' in block,
'no_force710':'no_force710=1' in block,
'no_force708':'no_force708=1' in block,
'no_action_rewrite':'no_action_rewrite=1' in block,
'no_char281_branch':not re.search(r'char(?:_id)?\s*==\s*281|cid\s*==\s*281',block),
'helper_order':cpp.find('bool MatchWords(')<cpp.find('InstallP100BRouteSweepInternal()') and cpp.find('void LogFingerprintFail(')<cpp.find('InstallP100BRouteSweepInternal()'),
}
for k,v in checks.items(): print(k,'PASS' if v else 'FAIL'); assert v,k
# exact source words against paired v1.70 main
p=(ROOT/'paired/atmosphere/contents/0100FA10190A0000/exefs/main').read_bytes(); base=0x101
words={0x488B24:0xAA0003F3,0x7E6500:0xAA0003F3,0x7E6520:0xB95C0388,0x7E664C:0xF9400268,0x7E6768:0xAA1303E0,0x7E6814:0xB95C0388,0x7E6880:0xD2A00000,0x7E6A58:0xAA1703FA,0x7E6B08:0xAA1803F6,0x7E6B10:0xAA1303E0,0x7E6BB4:0xB94E5668,0x7E6C34:0xAA1803F6,0x7E6C50:0x2A0003E1,0x7E6D0C:0xF9400268,0x7E6D58:0xAA1303E0,0x7E6EA8:0x528058C1}
for off,exp in words.items():
 got=int.from_bytes(p[base+off:base+off+4],'little'); assert got==exp,(hex(off),hex(got),hex(exp))
print('fingerprints PASS')
for rel,exp in [
('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),
('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]:
 got=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(); print(rel,got); assert got==exp
push=[]
for q in sorted((ROOT/'.github/workflows').glob('*.yml')):
 t=q.read_text()
 if re.search(r'(?m)^  push:\s*$',t): push.append(q.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p100b.yml']
wf=(ROOT/'.github/workflows/build-subsdk9-p100b.yml').read_text()
assert 'git -C exlaunch checkout --detach 229bbd6' in wf
assert 'NSC-P100B-one-shot-action710-route-sweep' in wf
print('P100B_DROPIN_SOURCE_VERIFY=PASS')
