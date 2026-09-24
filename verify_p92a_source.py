from pathlib import Path
import hashlib,re
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
checks={
'entrypoint':'nsc::InstallP92AFocusedHandoffStateSweep();' in main,
'decl':'void InstallP92AFocusedHandoffStateSweep();' in hpp,
'parent':'InstallP91AFocusedHandoffStateTrace();' in cpp,
'ready':'[NSC:P92A] READY' in cpp,
'sweep0':'[NSC:P92A] SWEEP0' in cpp,
'sweep1':'[NSC:P92A] SWEEP1' in cpp,
'zero_extra':'zero_extra_trampolines=1' in cpp,
'no_char281':'char_id == 281' not in cpp and 'char_id==281' not in cpp,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}'); assert v
expected={'paired/atmosphere/contents/0100FA10190A0000/exefs/main':'1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0','restore/atmosphere/contents/0100FA10190A0000/exefs/main':'2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'}
for f,h in expected.items():
 got=hashlib.sha256((root/f).read_bytes()).hexdigest(); print(f,got); assert got==h
push=[]
for p in (root/'.github/workflows').glob('*.yml'):
 s=p.read_text()
 if re.search(r'^\s*push\s*:',s,re.M): push.append(p.name)
print('push_enabled_workflows',sorted(push)); assert push==['build-subsdk9-p92a.yml']
print('P92A_DROPIN_SOURCE_VERIFY=PASS')
