from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()

start=cpp.find('// P104B — sibling-controller two-gate proof v2')
assert start>=0
block=cpp[start:]
hook_start=cpp.find('HOOK_DEFINE_TRAMPOLINE(P104BSiblingControllerGateHook)',start)
hook_end=cpp.find('static bool InstallP104BSiblingControllerGateTraceInternal()',hook_start)
assert hook_start>=0 and hook_end>hook_start
hook=cpp[hook_start:hook_end]

def pos(needle):
    i=hook.find(needle)
    assert i>=0,needle
    return i

p_exact=pos('const bool exact_caller = caller_off == kP104BSiblingPredicateReturn;')
p_identity=pos('ReadActorIdentity(actor, side, cid)')
p_pre=pos('gate12240_pre = *reinterpret_cast')
p_orig=pos('const uint32_t native_ret = Orig(actor);')
p_early=pos('if (!exact_caller || !valid_player)')
p_post=pos('const uint32_t gate12240_post =')
p_post_state=pos('const P93CoreState post = ReadP93CoreState(actor);')

checks={
 'entrypoint':'nsc::InstallP104BSiblingControllerGateTrace();' in main,
 'decl':'void InstallP104BSiblingControllerGateTrace();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P104B] READY' in block,
 'gate_log':'[NSC:P104B] GATE' in hook,
 'pred_offset':'kP104BSiblingPredicateOffset = 0x7EE8E0' in block,
 'caller_return':'kP104BSiblingPredicateReturn = 0x7DE028' in block,
 'gate_field':'kP104BGate12240Offset = 0x12240' in block,
 'one_p104b_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P104BSiblingControllerGateHook)')==1,
 'no_p104b_inline':'HOOK_DEFINE_INLINE(P104B' not in cpp,
 'orig_once_textual':len(re.findall(r'^\s*const uint32_t native_ret = Orig\(actor\);\s*$',hook,re.M))==1,
 'orig_actor':'const uint32_t native_ret = Orig(actor);' in hook,
 'exact_caller_before_actor_read':p_exact < p_identity,
 'gate_pre_before_orig':p_pre < p_orig,
 'gate_post_after_orig':p_orig < p_early < p_post,
 'gate_post_before_post_state':p_post < p_post_state,
 'player_side_only':'valid_player = valid && side == 0u;' in hook,
 'non_target_early_return':'if (!exact_caller || !valid_player)' in hook and 'return native_ret;' in hook[p_early:p_post],
 'focused_700_711':'pre.action >= 700u && pre.action <= 711u' in hook and 'post.action >= 700u && post.action <= 711u' in hook,
 'reads_gate_pre':'gate12240_pre' in hook and 'b + kP104BGate12240Offset' in hook,
 'reads_gate_post':'gate12240_post' in hook and hook.count('b + kP104BGate12240Offset')==2,
 'logs_gate_change':'gate12240_changed=%u' in hook,
 'logs_vslots':'slot4c0_off' in hook and 'slot520_off' in hook,
 'p103_absent':'[NSC:P103A]' not in cpp and 'P103SpecialCondFactoryBridgeHook' not in cpp,
 'p102_absent':'[NSC:P102A] HOLD74' not in cpp and 'P102IncrementHold74Count' not in cpp,
 'p101_absent':'P101State125GuardHook' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',hook),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',hook),
 'no_gate_write':not re.search(r'kP104BGate12240Offset[^;\n]*\)\s*=',hook),
 'no_state_control_write':not re.search(r'\+\s*0x(?:E94|E9C|EA4|BDA4|BDA8|BDC8)\)\s*=',hook,re.I),
 'no_char281_branch':not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',block),
 'p104a_runtime_marker_absent':'[NSC:P104A]' not in cpp,
}
for k,v in checks.items():
 print(k,'PASS' if v else 'FAIL'); assert v,k

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]
text_file=struct.unpack_from('<I',b,0x10)[0]
text_size=struct.unpack_from('<I',b,0x18)[0]
assert (flags&1)==0
text=b[text_file:text_file+text_size]
def word(off):return struct.unpack_from('<I',text,off)[0]
expected={
 0x7DDD94:0xD10243FF, 0x7DDD98:0xF90023FE,
 0x7DE020:0xAA1303E0, 0x7DE024:0x9400422F,
 0x7DE028:0x340024C0, 0x7DE02C:0xB95D86E8, 0x7DE030:0x34002488,
 0x7EE8E0:0xF81D0FFE, 0x7EE8E4:0xA90157F6, 0x7EE8E8:0xA9024FF4,
 0x7EE8EC:0xF9400008, 0x7EE8F0:0xAA0003F5, 0x7EE8F4:0xF946E908,
 0x7EE8F8:0xD63F0100, 0x7EE8FC:0xB40003C0,
 0x7E6EA8:0x528058C1,
}
for off,w in expected.items():
 got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w,(hex(off),hex(got),hex(w))
# Decode exact BL at 0x7DE024 and prove target 0x7EE8E0.
w=word(0x7DE024); imm=w&0x03ffffff
if imm&0x02000000:imm-=0x04000000
tgt=0x7DE024+imm*4
print('call 0x7DE024 ->',hex(tgt)); assert tgt==0x7EE8E0
# Decode LDR W8,[X23,#imm] at 0x7DE02C and prove effective actor+0x12240.
w=word(0x7DE02C); assert (w&0xFFC00000)==0xB9400000
imm12=(w>>10)&0xfff; rn=(w>>5)&31; rt=w&31
print('gate ldr imm',hex(imm12*4),'rn',rn,'rt',rt)
assert imm12*4==0x1D84 and rn==23 and rt==8
assert 0x104BC + imm12*4 == 0x12240

push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M):push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p104b.yml']
print('P104B_DROPIN_SOURCE_VERIFY=PASS')
