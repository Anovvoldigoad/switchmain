from pathlib import Path
import hashlib,re
r=Path('.')
s=(r/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
h=(r/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
m=(r/'overlay/source/program/main.cpp').read_text()
checks={
'entrypoint':'InstallP91AFocusedHandoffStateTrace();' in m,
'decl':'InstallP91AFocusedHandoffStateTrace();' in h,
'p89_parent':'InstallP89APhase3ActorPredBridge();' in s[s.index('void InstallP91AFocusedHandoffStateTrace'):],
'ready':'[NSC:P91A] READY' in s, 'handoff':'[NSC:P91A] HANDOFF' in s,
'zero_extra':'zero_extra_trampolines=1' in s,
'expanded':'s106f4=%08x->%08x' in s and 's123e0=%08x->%08x' in s and 's123e4=%08x->%08x' in s,
'corridor_fields':'e60=%08x->%08x' in s and 'e98=%08x->%08x' in s and 'e9c=%08x->%08x' in s and 'ea0=%08x->%08x' in s and 'ea4=%08x->%08x' in s,
'no_char281':'char_id == 281' not in s and 'char_id==281' not in s,
'no_force710':'index = 710' not in s,
}
for k,x in checks.items(): print(k,'PASS' if x else 'FAIL'); assert x
for rel,want in [('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]:
 got=hashlib.sha256((r/rel).read_bytes()).hexdigest(); print(rel,got); assert got==want
push=[]
for p in sorted((r/'.github/workflows').glob('*.yml')):
 t=p.read_text(); on=t.split('jobs:',1)[0];
 if re.search(r'^\s*push\s*:',on,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p91a.yml']
print('P91A_DROPIN_SOURCE_VERIFY=PASS')
