from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P124A — NATIVE-SAFE UJ CORRIDOR REACH PROOF')
assert start>=0
block=cpp[start:]
def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n
checks={
 'entrypoint':'nsc::InstallP124ANativeSafeUjCorridorReachProof();' in main,
 'decl':'void InstallP124ANativeSafeUjCorridorReachProof();' in hpp,
 'ready':'[NSC:P124A] READY' in block,
 'gate_log':'[NSC:P124A] GATE' in block,
 'after_actor_log':'[NSC:P124A] AFTER_ACTOR' in block,
 'after_peer_log':'[NSC:P124A] AFTER_PEER' in block,
 'type9_zero_log':'[NSC:P124A] TYPE9_ZERO' in block,
 'outer_reach_log':'[NSC:P124A] OUTER_REACH' in block,
 'compact_parent_p81':'InstallP81AOugiAwakeningPolicyBridge();' in block,
 'direct_p89':'InstallP89Internal();' in block,
 'no_p123_parent':'InstallP123ACompactConditionalOuterCorridorBridge();' not in block,
 'five_p124_inline':len(re.findall(r'HOOK_DEFINE_INLINE\(P124',block))==5,
 'zero_p124_trampoline':'HOOK_DEFINE_TRAMPOLINE(P124' not in block,
 'five_installat':len(re.findall(r'P124\w+Hook::InstallAtOffset',block))==5,
 'gate_77c474':'kP124GateLoadOffset = 0x77C474' in block,
 'actor_pass_77c498':'kP124ActorPassOffset = 0x77C498' in block,
 'peer_pass_77c4ac':'kP124PeerPassOffset = 0x77C4AC' in block,
 'type9_zero_77c514':'kP124Type9ZeroOffset = 0x77C514' in block,
 'outer_reach_77c5e4':'kP124OuterReachOffset = 0x77C5E4' in block,
 'replay_ldr_x8':'ctx->X[8]=vtbl' in block,
 'replay_mov_w0_9':'ctx->W[0]=9u' in block,
 'replay_mov_x0_x19':'ctx->X[0]=ctx->X[19]' in block,
 'replay_mov_x0_x23':'ctx->X[0]=ctx->X[23]' in block,
 'capture_actor_ret':'const uint32_t actor_ret = ctx->W[0]' in block,
 'capture_peer_ret':'const uint32_t peer_ret=ctx->W[0]' in block,
 'generic_custom':'q.ac > kVanillaMaxCharId' in block and 'ac > kVanillaMaxCharId' in block,
 'semantic707_arm':'semantic && action==707u' in block,
 'opposite_side':'q.opposite' in block and 'opposite' in block,
 'appended_damage':'kP124VanillaDamageCount = 1847u' in block,
 'no_callback_native_call':'P124CallNative' not in block and 'reinterpret_cast<P124Call' not in block,
 'native_calls_untouched_claim':'native_bl_blr_untouched=1' in block,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'p89_preserved':'[NSC:P89A] ACTOR_PRED' in cpp,
 'no_fixture_damage_strings':'"DMG_MTOB_SPL' not in block and '"DAMAGE_ID_SPATK_BEGIN_DIRECT' not in block,
 'no_char281_branch':not re.search(r'(?:char_id|cid|ac|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|ac|e54)',block),
}
for k,v in checks.items(): chk(k,v)
# No callsite hook at the native calls that regressed P123.
for forbidden in ('0x77C490','0x77C4A4','0x77C4B0','0x77C51C'):
    chk('no_hook_callsite_'+forbidden[2:].lower(), f'InstallAtOffset({forbidden})' not in block and f'= {forbidden};' not in block)
code_no_comments=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_game_pointer_write', not re.search(r'\*reinterpret_cast<[^>]+>\([^\n;]*\)\s*=',code_no_comments))
chk('no_b9e4_write','0xB9E4' not in code_no_comments and '0xb9e4' not in code_no_comments)
chk('no_session_create_call','0x7EF098' not in code_no_comments and '0x7ef098' not in code_no_comments)
chk('no_action_setter_call','kCentralActionSetterOffset' not in code_no_comments and '0x766320' not in code_no_comments)
chk('no_force708','force708' not in code_no_comments.lower())
chk('no_force710','force710' not in code_no_comments.lower())
for tag in ('GATE','AFTER_ACTOR','AFTER_PEER','TYPE9_ZERO','OUTER_REACH','READY'):
    calls=[x for x in re.findall(r'Logging\.Log\((.*?)\);',block,re.S) if f'[NSC:P124A] {tag}' in x]
    assert calls,tag
    x=calls[-1]; lits=re.findall(r'"((?:\\.|[^"\\])*)"',x)
    f=''.join(bytes(z,'utf8').decode('unicode_escape') for z in lits)
    total=0; last=0
    for m in re.finditer(r'%(?:0?8)?(?:l)?[duxps]',f):
        total+=len(f[last:m.start()]); sp=m.group(0)
        total+=11 if sp in ('%u','%d') else 8 if sp=='%08x' else 16 if sp=='%lx' else 18 if sp=='%p' else 96
        last=m.end()
    total+=len(f[last:])
    print('log_bound',tag,total); chk(tag.lower()+'_lt_512',total<512)
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
 0x77C490:0xD63F0100,0x77C494:0x34000AC0,0x77C498:0xF94002E8,
 0x77C4A4:0xD63F0100,0x77C4A8:0x34000A20,0x77C4AC:0x52800120,
 0x77C4B0:0x97FF50EC,0x77C4B4:0x34000300,0x77C514:0xAA1303E0,
 0x77C51C:0x9401ECF8,0x77C520:0xB40003E0,0x77C5E4:0xAA1703E0,0x77C5E8:0x9401CAAC,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    ss=p.read_text()
    if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p124a.yml']
assert 'exl::util::GetMainModuleInfo()' in block
assert 'exl::util::modules::GetMainModuleInfo()' not in cpp
print('main_module_info_api PASS')
print('P124A_DROPIN_SOURCE_VERIFY=PASS')
