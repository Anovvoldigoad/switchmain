from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P121B — BOOT-SAFE STATIC PEER-C48 BRANCH BYPASS A/B')
assert start>=0
block=cpp[start:]

def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n

checks={
 'entrypoint':'nsc::InstallP121BStaticPeerC48BranchBypass();' in main,
 'decl':'void InstallP121BStaticPeerC48BranchBypass();' in hpp,
 'ready':'[NSC:P121B] READY' in block,
 'parent_p120':'InstallP120ACustomUjCinematicGateBridge();' in block,
 'static_branch_offset':'kP121BPeerRejectBranchOffset = 0x77C4A8' in block,
 'native_peer_call_preserved':'0xD63F0100' in block,
 'patched_peer_cbz_nop':'0xD503201F' in block,
 'zero_p121_inline':'HOOK_DEFINE_INLINE(P121' not in cpp,
 'zero_p121_trampoline':'HOOK_DEFINE_TRAMPOLINE(P121' not in cpp,
 'zero_p121_installat':'P121CustomUjPeerC48Hook::InstallAtOffset' not in cpp and 'InstallAtOffset(kP121B' not in cpp,
 'p120_preserved':'[NSC:P120A] GATE' in cpp and cpp.count('P120CustomUjCinematicGateHook::InstallAtOffset')==1,
 'p120_only_new_runtime_hook':'one_new_inline_hook=1' in cpp and 'zero_new_trampoline_hooks=1' in cpp,
 'no_fixture_damage_strings':'"DMG_MTOB_SPL' not in block and '"DAMAGE_ID_SPATK_BEGIN_DIRECT' not in block,
 'no_char281_branch':not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)', block),
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force708':'force708' not in block.lower() or 'no_force708' in block,
 'no_force710':'force710' not in block.lower() or 'no_force710' in block,
}
for k,v in checks.items(): chk(k,v)

code_no_comments=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_game_pointer_write', not re.search(r'\*reinterpret_cast<[^>]+>\([^\n;]*\)\s*=', code_no_comments))
chk('no_b9e4_write','0xB9E4' not in code_no_comments and '0xb9e4' not in code_no_comments)
chk('no_session_create_call','0x7EF098' not in code_no_comments and '0x7ef098' not in code_no_comments)
chk('no_action_setter_call','kCentralActionSetterOffset' not in code_no_comments and '0x766320' not in code_no_comments)

# Conservative log bound for READY.
calls=[x for x in re.findall(r'Logging\.Log\((.*?)\);',block,re.S) if '[NSC:P121B] READY' in x]
assert calls
x=calls[-1]
lits=re.findall(r'"((?:\\.|[^"\\])*)"',x)
f=''.join(bytes(z,'utf8').decode('unicode_escape') for z in lits)
total=0; last=0
for m in re.finditer(r'%(?:0?8)?(?:l)?[duxps]',f):
    total += len(f[last:m.start()]); sp=m.group(0)
    if sp in ('%u','%d'): total+=11
    elif sp=='%08x': total+=8
    elif sp=='%lx': total+=16
    elif sp=='%p': total+=18
    elif sp=='%s': total+=96
    last=m.end()
total+=len(f[last:])
print('log_bound [NSC:P121B] READY',total); chk('ready_lt_512',total<512)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
paired_sha=sha(paired); restore_sha=sha(restore)
print('paired main',paired_sha); assert paired_sha=='f9a8a10f757987b353d7ddcf3a9a74621a8db2398fd6820d09ac280cae72070a'
print('restore main',restore_sha); assert restore_sha=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]
tf,tm,ts=struct.unpack_from('<III',b,0x10); assert (flags&1)==0
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,0x77C480:0x54000B81,
 0x77C484:0xF9400268,0x77C488:0xAA1303E0,0x77C48C:0xF9462508,0x77C490:0xD63F0100,
 0x77C494:0x34000AC0,0x77C498:0xF94002E8,0x77C49C:0xAA1703E0,0x77C4A0:0xF9462508,
 0x77C4A4:0xD63F0100,0x77C4A8:0xD503201F,0x77C4AC:0x52800120,0x77C4B0:0x97FF50EC,
 0x77C4B4:0x34000300,0x77C5E4:0xAA1703E0,0x77C5E8:0x9401CAAC,0x77C5EC:0xB9405288,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
# Restore must retain native peer reject branch.
br=restore.read_bytes(); tf2,tm2,ts2=struct.unpack_from('<III',br,0x10); text2=br[tf2:tf2+ts2]
assert struct.unpack_from('<I',text2,0x77C4A8)[0]==0x34000A20
print('restore_peer_cbz_native PASS')

push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    ss=p.read_text()
    if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p121b.yml']

assert 'exl::util::GetMainModuleInfo()' in cpp
assert 'exl::util::modules::GetMainModuleInfo()' not in cpp
print('main_module_info_api PASS')
print('P121B_DROPIN_SOURCE_VERIFY=PASS')
