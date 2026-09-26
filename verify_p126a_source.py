from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P126A — SINGLE ACTOR-C48 REJECT BYPASS')
assert start>=0
block=cpp[start:]
def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n
checks={
 'entrypoint':'nsc::InstallP126AActorC48RejectBypassProbe();' in main,
 'decl':'void InstallP126AActorC48RejectBypassProbe();' in hpp,
 'ready':'[NSC:P126A] READY' in block,
 'parent_p125':'InstallP125AP107GuidedSessionQualifiedState137Fallback();' in block,
 'zero_p126_inline':'HOOK_DEFINE_INLINE(P126' not in block,
 'zero_p126_trampoline':'HOOK_DEFINE_TRAMPOLINE(P126' not in block,
 'zero_p126_installat':'P126' not in ''.join(re.findall(r'\w+::InstallAtOffset\([^\n]+',block)),
 'actor_native_claim':'actor_c48_native_call_preserved=1' in block,
 'actor_reject_claim':'actor_reject_cbz_77c494_nopped=1' in block,
 'peer_native_claim':'peer_c48_native=1' in block and 'peer_reject_native=1' in block,
 'outer_native_claim':'native_7ef098=1' in block,
 'p125_qualified_claim':'p125_session_qualified_fallback=1' in block,
 'no_char281_branch':not re.search(r'(?:char_id|cid|ac|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|ac|e54)',block),
}
for k,v in checks.items(): chk(k,v)
# preserve functional baseline/source markers
chk('victim_shadows','VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp)
chk('p89','[NSC:P89A] ACTOR_PRED' in cpp)
chk('p124_gate','[NSC:P124A] GATE' in cpp)
chk('p124_after_actor','[NSC:P124A] AFTER_ACTOR' in cpp)
chk('p124_after_peer','[NSC:P124A] AFTER_PEER' in cpp)
chk('p124_type9','[NSC:P124A] TYPE9_ZERO' in cpp)
chk('p125_post_outer','[NSC:P125A] POST_OUTER' in cpp)
chk('p125_cleanup','[NSC:P125A] CLEANUP' in cpp)
# binary hashes/fingerprints
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
ps=sha(paired); rs=sha(restore)
print('paired main',ps)
EXPECTED_PAIRED='9ff3494b52a3ed2fd9af8879bbeec47806134a7607954c02ba622c2150fc06cf'
chk('paired_hash',ps==EXPECTED_PAIRED)
print('restore main',rs); chk('restore_hash',rs=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')
b=paired.read_bytes(); chk('nso0',b[:4]==b'NSO0')
flags=struct.unpack_from('<I',b,0x0C)[0]; tf,tm,ts=struct.unpack_from('<III',b,0x10); chk('text_uncompressed',(flags&1)==0)
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,0x77C480:0x54000B81,
 0x77C490:0xD63F0100,0x77C494:0xD503201F,0x77C498:0xF94002E8,
 0x77C4A4:0xD63F0100,0x77C4A8:0x34000A20,0x77C4AC:0x52800120,
 0x77C4B0:0x97FF50EC,0x77C4B4:0x34000300,0x77C514:0xAA1303E0,
 0x77C51C:0x9401ECF8,0x77C520:0xB40003E0,0x77C5E8:0x9401CAAC,0x77C5EC:0xB9405288,
 0x7EB27C:0x52800FA1,0x7EB288:0xD63F0100,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    s=p.read_text()
    if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); chk('only_p126_push',push==['build-subsdk9-p126a.yml'])
chk('main_module_api','exl::util::GetMainModuleInfo()' in cpp and 'exl::util::modules::GetMainModuleInfo()' not in cpp)
print('P126A_DROPIN_SOURCE_VERIFY=PASS')
