from pathlib import Path
import hashlib, re
ROOT = Path(__file__).resolve().parent
cpp = (ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp = (ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main = (ROOT/'overlay/source/program/main.cpp').read_text()
checks = {
    'entrypoint': 'nsc::InstallP96AActionDescriptorTransitionTrace();' in main,
    'decl': 'void InstallP96AActionDescriptorTransitionTrace();' in hpp,
    'parent_p95': 'void InstallP96AActionDescriptorTransitionTrace()' in cpp and 'InstallP95AQueuedActionParentTrace();' in cpp.split('void InstallP96AActionDescriptorTransitionTrace()',1)[1],
    'ready': '[NSC:P96A] READY' in cpp,
    'actdesc': '[NSC:P96A] ACTDESC' in cpp,
    'native_static_chain': all(x in cpp for x in ['current_action_766a98=1','mapper_769b04_e70=1','table_cache_7948e8=1','record_lookup_782c08=1','transition_selector_7efebc=1','string_resolver_3f5540_80efec=1']),
    'table_slot': '0x11660u' in cpp and 'static_cast<uintptr_t>(e90) * 8u' in cpp,
    'record_stride': '* 0x18u' in cpp,
    'descriptor_key': 'd + 0x94' in cpp and 'key707=' in cpp,
    'candidate_indices': all(x in cpp for x in ['707u, 791u, 833u, 875u','+ 84u','+ 126u','+ 168u']),
    'current_state': 'b + 0x218' in cpp and 'cur_state + 0x2C' in cpp,
    'mute_old_stack_scan': 'if (g_p96_descriptor_trace_mode) return;' in cpp and 'g_p96_descriptor_trace_mode = true;' in cpp,
    'no_p96_trampoline': 'HOOK_DEFINE_TRAMPOLINE(P96' not in cpp,
    'no_p96_inline_hook': 'HOOK_DEFINE_INLINE(P96' not in cpp,
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
assert push==['build-subsdk9-p96a.yml']
wf=(ROOT/'.github/workflows/build-subsdk9-p96a.yml').read_text()
assert 'git -C exlaunch checkout --detach 229bbd6' in wf
assert 'NSC-P96A-action-descriptor-transition-trace' in wf
assert "grep -aFq '[NSC:P96A] ACTDESC'" in wf
print('P96A_DROPIN_SOURCE_VERIFY=PASS')
