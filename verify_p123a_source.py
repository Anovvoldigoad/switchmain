from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P123A — COMPACT CONDITIONAL OUTER-CORRIDOR BRIDGE')
assert start>=0
block=cpp[start:]
def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n
checks={
 'entrypoint':'nsc::InstallP123ACompactConditionalOuterCorridorBridge();' in main,
 'decl':'void InstallP123ACompactConditionalOuterCorridorBridge();' in hpp,
 'ready':'[NSC:P123A] READY' in block,
 'gate_log':'[NSC:P123A] GATE' in block,
 'actor_log':'[NSC:P123A] ACTOR_C48' in block,
 'peer_log':'[NSC:P123A] PEER_C48' in block,
 'type9_log':'[NSC:P123A] TYPE9' in block,
 'lookup_log':'[NSC:P123A] LOOKUP' in block,
 'compact_parent_p81':'InstallP81AOugiAwakeningPolicyBridge();' in block,
 'direct_p89':'InstallP89Internal();' in block,
 'no_p96_parent':'InstallP96AActionDescriptorTransitionTrace();' not in block,
 'no_p120_parent':'InstallP120ACustomUjCinematicGateBridge();' not in block,
 'no_p121_parent':'InstallP121BStaticPeerC48BranchBypass();' not in block,
 'no_p122_parent':'InstallP122AStaticActorPeerC48BranchBypass();' not in block,
 'five_p123_inline':len(re.findall(r'HOOK_DEFINE_INLINE\(P123',block))==5,
 'zero_p123_trampoline':'HOOK_DEFINE_TRAMPOLINE(P123' not in block,
 'five_installat':len(re.findall(r'P123\w+Hook::InstallAtOffset',block))==5,
 'live_x23_attacker':'ctx->X[23]' in block,
 'victim_x19':'ctx->X[19]' in block,
 'generic_custom':'q.attacker_cid > kVanillaMaxCharId' in block and 'ac > kVanillaMaxCharId' in block,
 'semantic707':'q.semantic && q.action == 707u' in block and 'semantic && action==707u' in block,
 'opposite_side':'q.opposite' in block and 'opposite' in block,
 'appended_damage':'kP123VanillaDamageCount = 1847u' in block,
 'native_c48_once':'P123CallNative(target,ctx)' in block,
 'native_type9_once':'P123CallNative(base+kP123Type9Target,ctx)' in block,
 'native_lookup_once':'P123CallNative(base+kP123LookupTarget,ctx)' in block,
 'type9_false_overlay':'const bool bridge=q.active && native_ret!=0u;' in block and 'const uint32_t out=bridge?0u:native_ret;' in block,
 'lookup_null_overlay':'const uint64_t out=bridge?0u:native_ret;' in block,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'p89_semantic_bridge_preserved':'[NSC:P89A] ACTOR_PRED' in cpp,
 'no_fixture_damage_strings':'"DMG_MTOB_SPL' not in block and '"DAMAGE_ID_SPATK_BEGIN_DIRECT' not in block,
 'no_char281_branch':not re.search(r'(?:char_id|cid|ac|attacker_cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|ac|attacker_cid|e54)', block),
}
for k,v in checks.items(): chk(k,v)
code_no_comments=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_game_pointer_write', not re.search(r'\*reinterpret_cast<[^>]+>\([^\n;]*\)\s*=', code_no_comments))
chk('no_b9e4_write','0xB9E4' not in code_no_comments and '0xb9e4' not in code_no_comments)
chk('no_session_create_call','0x7EF098' not in code_no_comments and '0x7ef098' not in code_no_comments)
chk('no_action_setter_call','kCentralActionSetterOffset' not in code_no_comments and '0x766320' not in code_no_comments)
chk('no_force708','force708' not in code_no_comments.lower())
chk('no_force710','force710' not in code_no_comments.lower())
# Log bounds, conservative expansion.
for tag in ('GATE','ACTOR_C48','PEER_C48','TYPE9','LOOKUP','READY'):
    calls=[x for x in re.findall(r'Logging\.Log\((.*?)\);',block,re.S) if f'[NSC:P123A] {tag}' in x]
    assert calls,tag
    x=calls[-1]; lits=re.findall(r'"((?:\\.|[^"\\])*)"',x)
    f=''.join(bytes(z,'utf8').decode('unicode_escape') for z in lits)
    total=0; last=0
    for m in re.finditer(r'%(?:0?8)?(?:l)?[duxps]',f):
        total+=len(f[last:m.start()]); sp=m.group(0)
        total+=11 if sp in ('%u','%d') else 8 if sp=='%08x' else 16 if sp=='%lx' else 18 if sp=='%p' else 96
        last=m.end()
    total+=len(f[last:])
    print('log_bound',tag,total); chk(tag.lower()+'_lt_512', total<512)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
ps=sha(paired); rs=sha(restore)
print('paired main',ps); assert ps=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',rs); assert rs=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]; tf,tm,ts=struct.unpack_from('<III',b,0x10); assert (flags&1)==0
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,0x77C480:0x54000B81,
 0x77C484:0xF9400268,0x77C488:0xAA1303E0,0x77C48C:0xF9462508,0x77C490:0xD63F0100,
 0x77C494:0x34000AC0,0x77C498:0xF94002E8,0x77C49C:0xAA1703E0,0x77C4A0:0xF9462508,
 0x77C4A4:0xD63F0100,0x77C4A8:0x34000A20,0x77C4AC:0x52800120,0x77C4B0:0x97FF50EC,
 0x77C4B4:0x34000300,0x77C514:0xAA1303E0,0x77C518:0x9400666E,0x77C51C:0x9401ECF8,
 0x77C520:0xB40003E0,0x77C59C:0xF9400268,0x77C5E4:0xAA1703E0,0x77C5E8:0x9401CAAC,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    ss=p.read_text()
    if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p123a.yml']
assert 'exl::util::GetMainModuleInfo()' in block
assert 'exl::util::modules::GetMainModuleInfo()' not in cpp
print('main_module_info_api PASS')
print('P123A_DROPIN_SOURCE_VERIFY=PASS')
