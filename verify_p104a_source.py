from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()

start=cpp.find('// P104A — sibling-controller gate proof')
assert start>=0
block=cpp[start:]
hook_start=cpp.find('HOOK_DEFINE_TRAMPOLINE(P104SiblingControllerGateHook)',start)
hook_end=cpp.find('static bool InstallP104SiblingControllerGateTraceInternal()',hook_start)
assert hook_start>=0 and hook_end>hook_start
hook=cpp[hook_start:hook_end]
checks={
 'entrypoint':'nsc::InstallP104ASiblingControllerGateTrace();' in main,
 'decl':'void InstallP104ASiblingControllerGateTrace();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P104A] READY' in block,
 'gate_log':'[NSC:P104A] GATE' in hook,
 'pred_offset':'kP104SiblingPredicateOffset = 0x7EE8E0' in block,
 'caller_return':'kP104SiblingPredicateReturn = 0x7DE028' in block,
 'gate_field':'kP104Gate12240Offset = 0x12240' in block,
 'one_p104_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P104SiblingControllerGateHook)')==1,
 'no_p104_inline':'HOOK_DEFINE_INLINE(P104' not in cpp,
 'orig_once':hook.count('Orig(')==1,
 'orig_actor':'Orig(actor)' in hook,
 'exact_caller_gate':'caller_off == kP104SiblingPredicateReturn' in hook,
 'focused_700_711':'pre.action >= 700u && pre.action <= 711u' in hook,
 'reads_gate12240':'b + kP104Gate12240Offset' in hook,
 'logs_vslots':'slot4c0_off' in hook and 'slot520_off' in hook,
 'p103_absent':'[NSC:P103A]' not in cpp and 'P103SpecialCondFactoryBridgeHook' not in cpp,
 'p102_absent':'[NSC:P102A] HOLD74' not in cpp and 'P102IncrementHold74Count' not in cpp,
 'p101_absent':'P101State125GuardHook' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',hook),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',hook),
 'no_actor_field_write':not re.search(r'reinterpret_cast<volatile[^>]*>\([^\)]*\+\s*0xE54[^\)]*\)\s*=',hook,re.I),
 'no_gate_write':not re.search(r'kP104Gate12240Offset[^;\n]*\)\s*=',hook),
 'no_action_write':not re.search(r'\+\s*(?:4712|0x1268)\)\s*=',hook),
 'no_state_control_write':not re.search(r'\+\s*0x(?:E94|E9C|EA4|BDA4|BDA8|BDC8)\)\s*=',hook,re.I),
 'no_char281_branch':not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',block),
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
print('push_enabled_workflows',push); assert push==['build-subsdk9-p104a.yml']
print('P104A_DROPIN_SOURCE_VERIFY=PASS')
