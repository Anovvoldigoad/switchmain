from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P125A — P107-GUIDED, SESSION-QUALIFIED NATIVE STATE137 FALLBACK')
assert start>=0
block=cpp[start:]
p124_start=cpp.find('// P124A — NATIVE-SAFE UJ CORRIDOR REACH PROOF')
p124_block=cpp[p124_start:start]
def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n
checks={
 'entrypoint':'nsc::InstallP125AP107GuidedSessionQualifiedState137Fallback();' in main,
 'decl':'void InstallP125AP107GuidedSessionQualifiedState137Fallback();' in hpp,
 'ready':'[NSC:P125A] READY' in block,
 'post_outer_log':'[NSC:P125A] POST_OUTER' in block,
 'cleanup_log':'[NSC:P125A] CLEANUP' in block,
 'p124_gate_preserved':'[NSC:P124A] GATE' in p124_block,
 'p124_after_actor_preserved':'[NSC:P124A] AFTER_ACTOR' in p124_block,
 'p124_after_peer_preserved':'[NSC:P124A] AFTER_PEER' in p124_block,
 'p124_type9_preserved':'[NSC:P124A] TYPE9_ZERO' in p124_block,
 'compact_parent_p81':'InstallP81AOugiAwakeningPolicyBridge();' in block,
 'direct_p89':'InstallP89Internal();' in block,
 'no_p124_parent':'InstallP124ANativeSafeUjCorridorReachProof();' not in block,
 'two_p125_inline':len(re.findall(r'HOOK_DEFINE_INLINE\(P125',block))==2,
 'zero_p125_trampoline':'HOOK_DEFINE_TRAMPOLINE(P125' not in block,
 'two_p125_installat':len(re.findall(r'P125\w+Hook::InstallAtOffset',block))==2,
 'post_outer_77c5ec':'kP125PostOuterOffset = 0x77C5EC' in block,
 'cleanup_7eb27c':'kP125CleanupRequestOffset = 0x7EB27C' in block,
 'post_outer_replay_ldr':'ctx->W[8] = raw' in block,
 'cleanup_replay_mov':'ctx->W[1] = out' in block,
 'session_success_required':'outer_ret != 0u' in block and 'g_p125_session_actor' in block,
 'same_actor_session_latch':'g_p125_session_actor[side].load' in block,
 'mature_guard':'st.e94 == 136u' in block and 'st.e98 == 135u' in block and 'st.e9c == 0u' in block and 'st.bda4 == 0u' in block and 'st.bda8 == 0u' in block,
 'action708_guard':'action == 708u' in block,
 'generic_custom':'cid > kVanillaMaxCharId' in block,
 'semantic_guard':'P64QuerySemanticUltimateJutsu(actor)' in block,
 'native125_default':'const uint32_t out = bridge ? 137u : 125u' in block,
 'native_outer_call_untouched_claim':'native_7ef098_call_untouched=1' in block,
 'native_state_call_untouched_claim':'native_state_request_call_untouched=1' in block,
 'stale_p107_rejected_claim':'stale_p107_context_rejected=1' in block,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'p89_preserved':'[NSC:P89A] ACTOR_PRED' in cpp,
 'no_fixture_damage_strings':'"DMG_MTOB_SPL' not in block and '"DAMAGE_ID_SPATK_BEGIN_DIRECT' not in block,
 'no_char281_branch':not re.search(r'(?:char_id|cid|ac|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|ac|e54)',block),
}
for k,v in checks.items(): chk(k,v)
# P125 must leave all native calls untouched. It hooks only simple instructions.
for forbidden in ('0x77C490','0x77C4A4','0x77C4B0','0x77C51C','0x77C5E8','0x7EB288'):
    chk('no_hook_callsite_'+forbidden[2:].lower(), f'InstallAtOffset({forbidden})' not in block and f'= {forbidden};' not in block)
chk('p124_outer_pre_hook_not_installed','InstallP124OuterReach()' not in block)
code_no_comments=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_game_pointer_write', not re.search(r'\*reinterpret_cast<[^>]+>\([^\n;]*\)\s*=',code_no_comments))
chk('no_b9e4_write','0xB9E4' not in code_no_comments and '0xb9e4' not in code_no_comments)
chk('no_direct_7ef098_call','0x7EF098' not in code_no_comments and '0x7ef098' not in code_no_comments)
chk('no_action_setter_call','kCentralActionSetterOffset' not in code_no_comments and '0x766320' not in code_no_comments)
chk('no_force710','force710' not in code_no_comments.lower())
chk('no_orig_call','Orig(' not in block)
# Logging strings must fit svc debug string budget.
for tag in ('POST_OUTER','CLEANUP','READY'):
    calls=[x for x in re.findall(r'Logging\.Log\((.*?)\);',block,re.S) if f'[NSC:P125A] {tag}' in x]
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
 0x77C51C:0x9401ECF8,0x77C520:0xB40003E0,0x77C5E8:0x9401CAAC,0x77C5EC:0xB9405288,
 0x7EB27C:0x52800FA1,0x7EB280:0xAA0003F3,0x7EB284:0xF946F908,0x7EB288:0xD63F0100,
 0x7E6EC4:0x97FDFF32,0x7E6EC8:0x340004C0,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    ss=p.read_text()
    if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p125a.yml']
assert 'exl::util::GetMainModuleInfo()' in cpp
assert 'exl::util::modules::GetMainModuleInfo()' not in cpp
print('main_module_info_api PASS')
print('P125A_DROPIN_SOURCE_VERIFY=PASS')
