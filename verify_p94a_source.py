from pathlib import Path
import hashlib, re
ROOT = Path(__file__).resolve().parent
cpp = (ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp = (ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main = (ROOT/'overlay/source/program/main.cpp').read_text()
checks = {
    'entrypoint': 'nsc::InstallP94ASequenceControllerTrace();' in main,
    'decl': 'void InstallP94ASequenceControllerTrace();' in hpp,
    'parent_p93': 'void InstallP94ASequenceControllerTrace()' in cpp and 'InstallP93AMaxUsefulTrace();' in cpp.split('void InstallP94ASequenceControllerTrace()',1)[1],
    'ready': '[NSC:P94A] READY' in cpp,
    'seqctrl': '[NSC:P94A] SEQCTRL' in cpp,
    'seqvec': '[NSC:P94A] SEQVEC' in cpp,
    'controller_fields': all(x in cpp for x in ['0x12460','0x12468','0x1246C','0x12500','0x12504','0x12320']),
    'vectors': all(x in cpp for x in ['0x12470','0x124A0','0x124D0']),
    'vec_items': all(x in cpp for x in ['v.h0','v.h5','v.prev','v.cur','v.next']),
    'static_proof_note': all(x in cpp for x in ['main+0x48F18','main+0x772594','main+0x48FE0']),
    'no_p94_hook_define': 'HOOK_DEFINE_TRAMPOLINE(P94' not in cpp,
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
assert push==['build-subsdk9-p94a.yml']
wf=(ROOT/'.github/workflows/build-subsdk9-p94a.yml').read_text()
assert 'git -C exlaunch checkout --detach 229bbd6' in wf
assert 'NSC-P94A-sequence-controller-zero-extra-trace' in wf
print('P94A_DROPIN_SOURCE_VERIFY=PASS')
