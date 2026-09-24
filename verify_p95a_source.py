from pathlib import Path
import hashlib, re
ROOT = Path(__file__).resolve().parent
cpp = (ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp = (ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main = (ROOT/'overlay/source/program/main.cpp').read_text()
checks = {
    'entrypoint': 'nsc::InstallP95AQueuedActionParentTrace();' in main,
    'decl': 'void InstallP95AQueuedActionParentTrace();' in hpp,
    'parent_p94': 'void InstallP95AQueuedActionParentTrace()' in cpp and 'InstallP94ASequenceControllerTrace();' in cpp.split('void InstallP95AQueuedActionParentTrace()',1)[1],
    'ready': '[NSC:P95A] READY' in cpp,
    'queuectrl': '[NSC:P95A] QUEUECTRL' in cpp,
    'wrapper_parent': '[NSC:P95A] WRAPPER_PARENT' in cpp,
    'queue_fields': all(x in cpp for x in ['0x104DC','0x104E0','0x105F4','0x105F8','0x105FC','0x10600','0x10610']),
    'vslot_eb0': 'vtable + 0xEB0' in cpp and '0xF9475908u' in cpp,
    'parent_candidates': all(x in cpp for x in ['0x48FE4','0x7732A8','0x7EFF8C']),
    'stack_capture': 'asm volatile("mov %0, sp"' in cpp and 'kScanBytes' in cpp,
    'call_decode': 'P95IsBl' in cpp and 'P95IsBlr' in cpp,
    'no_p95_trampoline': 'HOOK_DEFINE_TRAMPOLINE(P95' not in cpp,
    'no_p95_inline_hook': 'HOOK_DEFINE_INLINE(P95' not in cpp,
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
assert push==['build-subsdk9-p95a.yml']
wf=(ROOT/'.github/workflows/build-subsdk9-p95a.yml').read_text()
assert 'git -C exlaunch checkout --detach 229bbd6' in wf
assert 'NSC-P95A-queued-action-parent-zero-extra-trace' in wf
assert "grep -aFq '[NSC:P95A] WRAPPER_PARENT'" in wf
print('P95A_DROPIN_SOURCE_VERIFY=PASS')
