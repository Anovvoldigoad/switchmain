from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P127A — FULL NATIVE CORRIDOR A/B')
assert start>=0
block=cpp[start:]
def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n
checks={
 'entrypoint':'nsc::InstallP127AFullNativeCorridorAB();' in main,
 'decl':'void InstallP127AFullNativeCorridorAB();' in hpp,
 'ready':'[NSC:P127A] READY' in block,
 'parent_p125':'InstallP125AP107GuidedSessionQualifiedState137Fallback();' in block,
 'robust_latch':'q.active = q.armed && q.custom;' in cpp,
 'strict_arm_still_present':'custom && semantic && action==707u && opposite && appended && !native_gate10' in cpp,
 'zero_p127_inline':'HOOK_DEFINE_INLINE(P127' not in block,
 'zero_p127_trampoline':'HOOK_DEFINE_TRAMPOLINE(P127' not in block,
 'zero_p127_installat':'P127' not in ''.join(re.findall(r'\w+::InstallAtOffset\([^\n]+',block)),
 'native_call_claims':all(x in block for x in ['native_actor_c48_call=1','native_peer_c48_call=1','native_type9_call=1','native_lookup_call=1','native_7ef098_call=1']),
 'branch_claims':all(x in block for x in ['actor_reject_open=1','peer_reject_open=1','type9_zero_path_forced=1','lookup_null_path_forced=1']),
 'p125_qualified':'p125_session_qualified_fallback=1' in block,
 'no_direct_outer':'no_direct_7ef098_call=1' in block,
 'no_force710':'no_force710=1' in block,
 'no_char281_branch':not re.search(r'(?:char_id|cid|ac|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|ac|e54)',block),
}
for k,v in checks.items(): chk(k,v)
for marker in ['VIS_SHADOW','CTRL14_SHADOW','[NSC:P89A] ACTOR_PRED','[NSC:P124A] GATE','[NSC:P124A] AFTER_ACTOR','[NSC:P124A] AFTER_PEER','[NSC:P124A] TYPE9_ZERO','[NSC:P125A] POST_OUTER','[NSC:P125A] CLEANUP']:
    chk('preserve_'+marker.replace('[','').replace(']','').replace(':','_').replace(' ','_'), marker in cpp)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
ps=sha(paired); rs=sha(restore)
print('paired main',ps)
EXPECTED='0dc14b32e125d5cef82225532b552722c8ddabb7b4b3ac1b93f500534f6c9367'
chk('paired_hash',ps==EXPECTED)
print('restore main',rs); chk('restore_hash',rs=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')
b=paired.read_bytes(); chk('nso0',b[:4]==b'NSO0')
flags=struct.unpack_from('<I',b,0x0C)[0]; tf,tm,ts=struct.unpack_from('<III',b,0x10); chk('text_uncompressed',(flags&1)==0)
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,0x77C480:0x54000B81,
 0x77C490:0xD63F0100,0x77C494:0xD503201F,0x77C498:0xF94002E8,
 0x77C4A4:0xD63F0100,0x77C4A8:0xD503201F,0x77C4AC:0x52800120,
 0x77C4B0:0x97FF50EC,0x77C4B4:0x14000018,0x77C514:0xAA1303E0,
 0x77C51C:0x9401ECF8,0x77C520:0x1400001F,0x77C59C:0xF9400268,
 0x77C5E8:0x9401CAAC,0x77C5EC:0xB9405288,
 0x7EB27C:0x52800FA1,0x7EB288:0xD63F0100,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
# prove four native call instructions are still call instructions
for off,w in [(0x77C490,0xD63F0100),(0x77C4A4,0xD63F0100),(0x77C4B0,0x97FF50EC),(0x77C51C,0x9401ECF8),(0x77C5E8,0x9401CAAC)]:
    chk('native_call_preserved_'+hex(off),word(off)==w)
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    s=p.read_text()
    if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); chk('only_p127_push',push==['build-subsdk9-p127a.yml'])
chk('main_module_api','exl::util::GetMainModuleInfo()' in cpp and 'exl::util::modules::GetMainModuleInfo()' not in cpp)
print('P127A_DROPIN_SOURCE_VERIFY=PASS')
