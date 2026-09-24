from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P102A — functional exact-callsite')
block=cpp[start:]
play_start=cpp.find('HOOK_DEFINE_TRAMPOLINE(PlayActionProbeHook)')
play_end=cpp.find('// P64F-A:',play_start)
play=cpp[play_start:play_end]
checks={
 'entrypoint':'nsc::InstallP102AExactFallback74SuppressionCandidate();' in main,
 'decl':'void InstallP102AExactFallback74SuppressionCandidate();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'p101_not_installed':'InstallP101AEventDriven708EndGuard();' not in main,
 'ready':'[NSC:P102A] READY' in cpp,
 'hold74_log':'[NSC:P102A] HOLD74' in play,
 'failopen74_log':'[NSC:P102A] FAILOPEN74' in play,
 'exact_caller':'kP102Fallback74CallerReturn = 0x798F34' in play,
 'index74_gate':'index == 74' in play,
 'action708_gate':'pre_action == 708u' in play,
 'semantic_gate':'P64QuerySemanticUltimateJutsu(actor)' in play,
 'membership_gate':'p81_data::ContainsOugiAwakeningId(char_id)' in play,
 'state_fingerprint':all(x in play for x in ['pre_e98 == 63u','pre_e9c == 0u','pre_bda4 == 1u','pre_bdc8 == 0u']),
 'bounded_16':'kP102MaxHold74Calls = 16u' in play and 'hold_n <= kP102MaxHold74Calls' in play,
 'same_native_success_ret':'return 1;' in play,
 'zero_new_p102_trampoline':'HOOK_DEFINE_TRAMPOLINE(P102' not in cpp and 'HOOK_DEFINE_INLINE(P102' not in cpp,
 'p101_state_guard_absent':'HOOK_DEFINE_TRAMPOLINE(P101State125GuardHook)' not in cpp,
 'no_active_p101_logs':'[NSC:P101A]' not in cpp,
 'no_p101_op23_helpers':all(x not in cpp for x in ['kP101Op23SeenBit','P101SetOp23Seen','P101QueryOp23Seen']),
 'victim_shadow_preserved':'case 12:' in cpp and 'VIS_SHADOW' in cpp and 'case 14:' in cpp and 'CTRL14_SHADOW' in cpp,
 'event23_normal':'case 23: // source me_play_action' in cpp and 'return HandleActionAnimation(actor, event, p2, p3, true);' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|index\s*=\s*710|return\s+710',block+play),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|index\s*=\s*708|return\s+708',block+play),
 'no_action_field_write':not re.search(r'\+\s*(?:4712|0x1268)\)\s*=',play),
 'no_e94_write':not re.search(r'\+\s*0xE94\)\s*=',play,re.I),
 'no_bda4_write':not re.search(r'\+\s*0xBDA4\)\s*=',play,re.I),
 'no_char281_branch':not re.search(r'(?:char_id|cid)\s*==\s*281|281\s*==\s*(?:char_id|cid)',play+block),
}
for k,v in checks.items():
 print(k,'PASS' if v else 'FAIL'); assert v,k

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
# Binary proof of exact fallback sequence in pinned paired main. Text starts at file+0x101.
b=paired.read_bytes()
def word(off): return struct.unpack_from('<I',b,0x101+off)[0]
expected={
 0x798E68:0xB94E9A68, # LDR W8,[X19,#E98]
 0x798E6C:0x52800941, # MOV W1,#74
 0x798E70:0x7101F11F, # CMP W8,#124
 0x798E74:0x54000541, # B.NE 0x798F1C
 0x798F1C:0x1E2E1000, # FMOV S0,#1.0
 0x798F20:0x12800002, # MOV W2,#-1
 0x798F24:0xAA1303E0, # MOV X0,X19
 0x798F28:0x2A1F03E3, # MOV W3,WZR
 0x798F2C:0x2A1F03E4, # MOV W4,WZR
 0x798F30:0x97FF3717, # BL PlayAction
 0x798F34:0xB94E5668, # next instruction / runtime LR
}
for off,w in expected.items():
 got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p102a.yml']
print('P102A_DROPIN_SOURCE_VERIFY=PASS')
