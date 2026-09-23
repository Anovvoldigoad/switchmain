from pathlib import Path
import hashlib, sys
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
checks={
 'entrypoint':'nsc::InstallP90ACinematicHandoffTrace();' in main,
 'decl':'void InstallP90ACinematicHandoffTrace();' in hpp,
 'p89_parent':'InstallP89APhase3ActorPredBridge();' in cpp,
 'p89_bridge':'kP89ActorPred = 0x7E24EC' in cpp and 'p81_data::ContainsOugiAwakeningId(cid)' in cpp,
 'lookup':'kP90ActionLookup = 0x768E84' in cpp,
 'gate':'kP90ActionGate   = 0x769A4C' in cpp,
 'lookup_marker':'[NSC:P90A] LOOKUP' in cpp,
 'gate_marker':'[NSC:P90A] GATE' in cpp,
 'ready_marker':'[NSC:P90A] READY' in cpp,
 'ea4_snapshot':'b + 0xEA4' in cpp,
 'caller_capture':'asm volatile("mov %0, x30"' in cpp,
 'no_char281':'cid == 281' not in cpp and 'cid==281' not in cpp,
 'no_force708':'no_force708=1' in cpp,
 'no_double_playaction':'P90ActionPlay' not in cpp,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)
for rel,want in [
 ('paired/atmosphere/contents/0100FA10190A0000/exefs/main','1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),
 ('restore/atmosphere/contents/0100FA10190A0000/exefs/main','2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]:
 p=root/rel; got=hashlib.sha256(p.read_bytes()).hexdigest(); print(rel,got); assert got==want
w=sorted((root/'.github/workflows').glob('*.yml'))
print('workflow_count',len(w),[p.name for p in w])
assert (root/'.github/workflows/build-subsdk9-p90a.yml').is_file()
push_enabled=[]
for wf in w:
    txt=wf.read_text()
    if 'push:' in txt:
        push_enabled.append(wf.name)
print('push_enabled_workflows',push_enabled)
assert push_enabled==['build-subsdk9-p90a.yml'], push_enabled
for old in ['build-subsdk9-p87a.yml','build-subsdk9-p88a.yml','build-subsdk9-p89a.yml']:
    p=root/'.github/workflows'/old
    if p.exists():
        txt=p.read_text()
        assert 'workflow_dispatch:' in txt and 'push:' not in txt, old
print('P90A_DROPIN_SOURCE_VERIFY=PASS')
