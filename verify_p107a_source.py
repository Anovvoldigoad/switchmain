from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P107A — exact post-708 cleanup-state bridge')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P107StateRequestBridgeHook)',start)
he=cpp.find('static bool InstallP107StateRequestBridgeInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('state_req_abi','static uint32_t Callback(void* actor, uint32_t requested_state' in h and 'uint32_t arg2, uint32_t arg3)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('fast_filter_before_actor',pos(h,'if (caller_off != kP107CleanupCallerReturn || requested_state != kP107CleanupState)') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('orig_two_exclusive_paths',len(re.findall(r'\bOrig\s*\(',h))==2)
chk('fast_passthrough','return Orig(actor, requested_state, arg2, arg3);' in h)
chk('mapped_orig_once','const uint32_t ret = Orig(actor, mapped_state, arg2, arg3);' in h)
chk('map_after_guard',pos(h,'const bool bridge =') < pos(h,'const uint32_t mapped_state = bridge ? kP107HandoffState : requested_state;'))
chk('post_after_orig',pos(h,'const uint32_t ret = Orig(') < pos(h,'const P93CoreState post ='))
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
checks={
 'entrypoint':'nsc::InstallP107Post708StateBridge();' in main,
 'decl':'void InstallP107Post708StateBridge();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P107A] READY' in block,
 'bridge_log':'[NSC:P107A] BRIDGE' in block,
 'state_request_offset':'kP107StateRequestOffset = 0x7A89A4' in block,
 'cleanup_caller':'kP107CleanupCallerReturn = 0x7EB28C' in block,
 'cleanup_125':'kP107CleanupState = 125u' in block,
 'handoff_137':'kP107HandoffState = 137u' in block,
 'one_p107_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P107')==1,
 'no_p107_inline':'HOOK_DEFINE_INLINE(P107' not in cpp,
 'exact_args':'arg2 == 1u && arg3 == 0u' in block,
 'exact_action708':'pre.action == 708u' in block,
 'exact_prestate':'pre.e94 == 63u && pre.e98 == 136u && pre.e9c == 0u' in block,
 'exact_controlstate':'pre.bda4 == 1u && pre.bda8 == 0u && pre.bdc8 == 0u' in block,
 'semantic_gate':'P64QuerySemanticUltimateJutsu(actor)' in block,
 'membership_gate':'p81_data::ContainsOugiAwakeningId(cid)' in block,
 'player_side_only':'side == 0u' in block,
 'p106_runtime_absent':'[NSC:P106A]' not in cpp and 'P106Controller520Hook' not in cpp,
 'p105b_runtime_absent':'[NSC:P105B]' not in cpp and 'P105BController4C0Hook' not in cpp,
 'p105a_runtime_absent':'[NSC:P105A]' not in cpp,
 'p104_runtime_absent':'[NSC:P104B]' not in cpp and '[NSC:P104A]' not in cpp,
 'p103_absent':'[NSC:P103A]' not in cpp and 'P103SpecialCondFactoryBridgeHook' not in cpp,
 'p102_hold74_absent':'[NSC:P102A] HOLD74' not in cpp,
 'p101_hold125_absent':'P101State125GuardHook' not in cpp and '[NSC:P101A] HOLD125' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',block),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',block),
 'no_direct_state_write':not re.search(r'reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only),
 'no_char281_branch':not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',block),
 'return_native_ret':'return ret;' in h,
}
for k,v in checks.items(): chk(k,v)
# Conservative P107 logger bound. LoggerMgr buffer is 512 bytes.
def bounds(src):
 out=[]
 for m in re.finditer(r'Logging\.Log\((.*?)\);',src,re.S):
  expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
  if not lits: continue
  fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
  if '[NSC:P107A]' not in fmt: continue
  total=0; last=0
  for fm in re.finditer(r'%(?:0?8)?(?:l)?[uxp]',fmt):
   total+=len(fmt[last:fm.start()]); sp=fm.group(0)
   total+=10 if sp=='%u' else 8 if sp=='%08x' else 16 if sp=='%lx' else 18
   last=fm.end()
  total+=len(fmt[last:]); out.append((fmt.split()[1],total))
 return out
bds=bounds(block); print('p107_log_bounds',bds); chk('p107_log_buffer_guard',bool(bds) and all(n<512 for _,n in bds))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]; tf=struct.unpack_from('<I',b,0x10)[0]; ts=struct.unpack_from('<I',b,0x18)[0]
assert (flags&1)==0
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x7A89A4:0xA9BD5FFE,0x7A89A8:0xA90157F6,0x7A89AC:0xA9024FF4,0x7A89B0:0x2A0103F4,
 0x7A89B4:0xAA0003F3,0x7A89B8:0x34000282,0x7A89BC:0xF9400268,0x7A89C0:0xAA1303E0,
 0x7EB270:0xF81E0FFE,0x7EB274:0xA9014FF4,0x7EB278:0xF9400008,0x7EB27C:0x52800FA1,
 0x7EB280:0xAA0003F3,0x7EB284:0xF946F908,0x7EB288:0xD63F0100,0x7EB28C:0xF9400268,
 0x7A8310:0xB94E9675,0x7A834C:0x2A1F03E1,0x7A8350:0xD63F0100,
 0x7E64D4:0xD10683FF,0x7E6EA8:0x528058C1,0x7E6EC4:0x97FDFF32,
}
for off,w in expected.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
# Prove exact cleanup producer encodes state125.
w=word(0x7EB27C); assert (w & 0x7F800000)==0x52800000
imm16=(w>>5)&0xFFFF; print('cleanup_mov_state',imm16); assert imm16==125
# Prove native 710 call still targets PlayAction.
def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
g=bl_target(0x7E6EC4); print('call',hex(0x7E6EC4),'->',hex(g)); assert g==0x766B8C
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p107a.yml']
print('P107A_DROPIN_SOURCE_VERIFY=PASS')
