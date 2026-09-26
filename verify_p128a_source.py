from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P128A — STATIC PRECISE GATE CAVE')
assert start>=0
block=cpp[start:]
def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n
checks={
 'entrypoint':'nsc::InstallP128AStaticPreciseGateCaveProof();' in main,
 'decl':'void InstallP128AStaticPreciseGateCaveProof();' in hpp,
 'ready':'[NSC:P128A] READY' in block,
 'post_outer':'[NSC:P128A] POST_OUTER' in block,
 'persistent_latch':'g_p128_gate_actor' in cpp,
 'strict_gate_arm':'strict_candidate = custom && semantic && action==707u && opposite && appended && as<=1u' in cpp,
 'compact_install':'const bool gate=InstallP124Gate();' in block and 'const bool post=InstallP128PostOuter();' in block and 'const bool cleanup=InstallP125CleanupRequest();' in block,
 'no_after_actor_install':'InstallP124ActorPass()' not in block,
 'no_after_peer_install':'InstallP124PeerPass()' not in block,
 'no_type9_hook_install':'InstallP124Type9Zero()' not in block,
 'no_outer_reach_install':'InstallP124OuterReach()' not in block,
 'runtime_fingerprint':'rt480=%08x' in block and 'rt4b8=%08x' in block and 'rt5e8=%08x' in block,
 'raw_policy_claim':'raw10_11_native=1 raw15_custom_action707=1 raw24_rejected=1' in block,
 'no_direct_outer':'no_direct_7ef098_call=1' in block,
 'no_force710':'no_force710=1' in block,
 'no_force708':'no_force708=1' in block,
 'no_char281_branch':not re.search(r'(?:char_id|cid|ac|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|ac|e54)',block),
}
for k,v in checks.items(): chk(k,v)
for marker in ['VIS_SHADOW','CTRL14_SHADOW','[NSC:P89A] ACTOR_PRED','[NSC:P124A] GATE','[NSC:P125A] CLEANUP']:
    chk('preserve_'+marker.replace('[','').replace(']','').replace(':','_').replace(' ','_'), marker in cpp)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
ps=sha(paired); rs=sha(restore)
print('paired main',ps)
EXPECTED='904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff'
chk('paired_hash',ps==EXPECTED)
print('restore main',rs); chk('restore_hash',rs=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')
b=paired.read_bytes(); chk('nso0',b[:4]==b'NSO0')
flags=struct.unpack_from('<I',b,0x0C)[0]; tf,tm,ts=struct.unpack_from('<III',b,0x10); chk('text_uncompressed',(flags&1)==0)
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,0x77C480:0x1400000E,
 0x77C490:0xD63F0100,0x77C494:0xD503201F,0x77C4A4:0xD63F0100,0x77C4A8:0xD503201F,
 0x77C4B0:0x97FF50EC,0x77C4B4:0x14000018,
 0x77C4B8:0x7100291F,0x77C4BC:0x54000220,0x77C4C0:0x71002D1F,0x77C4C4:0x540001E0,
 0x77C4C8:0x71003D1F,0x77C4CC:0x54000181,0x77C4D0:0xB94E56EA,0x77C4D4:0x7104615F,
 0x77C4D8:0x54000129,0x77C4DC:0x7140055F,0x77C4E0:0x540000E2,0x77C4E4:0xF9410EEA,
 0x77C4E8:0xB40000AA,0x77C4EC:0xB9402D4A,0x77C4F0:0x710B0D5F,0x77C4F4:0x54000041,
 0x77C4F8:0x14000002,0x77C4FC:0x1400003D,0x77C500:0x17FFFFE1,
 0x77C514:0xAA1303E0,0x77C51C:0x9401ECF8,0x77C520:0x1400001F,0x77C59C:0xF9400268,
 0x77C5E8:0x9401CAAC,0x77C5EC:0xB9405288,0x7EB27C:0x52800FA1,0x7EB288:0xD63F0100,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
# downstream native calls preserved
for off,w in [(0x77C490,0xD63F0100),(0x77C4A4,0xD63F0100),(0x77C4B0,0x97FF50EC),(0x77C51C,0x9401ECF8),(0x77C5E8,0x9401CAAC)]:
    chk('native_call_preserved_'+hex(off),word(off)==w)
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    s=p.read_text()
    if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); chk('only_p128_push',push==['build-subsdk9-p128a.yml'])
chk('main_module_api','exl::util::GetMainModuleInfo()' in cpp and 'exl::util::modules::GetMainModuleInfo()' not in cpp)
print('P128A_DROPIN_SOURCE_VERIFY=PASS')
