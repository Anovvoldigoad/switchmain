from pathlib import Path
import hashlib, re
ROOT = Path(__file__).resolve().parent
cpp = (ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp = (ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main = (ROOT/'overlay/source/program/main.cpp').read_text()
checks = {
    'entrypoint': 'nsc::InstallP93AMaxUsefulTrace();' in main,
    'decl': 'void InstallP93AMaxUsefulTrace();' in hpp,
    'parent_p92': 'void InstallP93AMaxUsefulTrace()' in cpp and 'InstallP92AFocusedHandoffStateSweep();' in cpp.split('void InstallP93AMaxUsefulTrace()',1)[1],
    'ready': '[NSC:P93A] READY' in cpp,
    'core': '[NSC:P93A] CORE' in cpp,
    'wide_state': all(x in cpp for x in ['st.e90','st.e94','st.e98','st.e9c','st.ea4','st.bda4','st.bdc8','st.s106f4','st.s123e0','st.s123e4']),
    'existing_hook_tags': all(x in cpp for x in ['PLAYACTION','CENTRAL_SETTER','MODE_BASE','P81_POLICY','P77_UJ_ACCEPT','P88B_HELPER','P89_ACTOR_PRED','EVT236_PRE']),
    'no_p93_hook_define': 'HOOK_DEFINE_TRAMPOLINE(P93' not in cpp,
    'no_force710': 'no_force710=1' in cpp,
    'no_force708': 'no_force708=1' in cpp,
    'no_char281_branch': not re.search(r'char(?:_id)?\s*==\s*281|cid\s*==\s*281', cpp),
}
for k,v in checks.items():
    print(k, 'PASS' if v else 'FAIL')
    assert v, k
pairs = [
    ('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),
    ('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'),
]
for rel,exp in pairs:
    got=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    print(rel, got)
    assert got==exp
push=[]
for p in sorted((ROOT/'.github/workflows').glob('*.yml')):
    t=p.read_text()
    if re.search(r'(?m)^\s{2}push:\s*$', t): push.append(p.name)
print('push_enabled_workflows',push)
assert push==['build-subsdk9-p93a.yml']
assert 'git -C exlaunch checkout --detach 229bbd6' in (ROOT/'.github/workflows/build-subsdk9-p93a.yml').read_text()
print('P93A_DROPIN_SOURCE_VERIFY=PASS')
