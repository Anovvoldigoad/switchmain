from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P111A — victim / participant state provenance probe')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P111VictimStateProvenanceHook)',start)
he=cpp.find('static bool InstallP111VictimStateProvenanceInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('state_req_abi','static uint32_t Callback(void* actor, uint32_t requested_state' in h and 'uint32_t arg2, uint32_t arg3)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('focus_before_actor',pos(h,'if (!focused)') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('orig_two_textual_paths',len(re.findall(r'\bOrig\s*\(',h))==2)
chk('fast_passthrough','return Orig(actor, requested_state, arg2, arg3);' in h)
chk('focused_orig_unchanged','const uint32_t ret = Orig(actor, requested_state, arg2, arg3);' in h)
chk('post_after_orig',pos(h,'const uint32_t ret = Orig(') < pos(h,'const P93CoreState post ='))
checks={
 'entrypoint':'nsc::InstallP111VictimStateProvenanceProbe();' in main,
 'decl':'void InstallP111VictimStateProvenanceProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P111A] READY' in block,
 'vstate_log':'[NSC:P111A] VSTATE' in block,
 'state_request_offset':'kP111StateRequestOffset = 0x7A89A4' in block,
 'simple_setter_offset':'kP111SimpleE9CSetterOffset = 0x7A8A9C' in block,
 'focus39':'kP111State39  = 39u' in block,
 'focus81':'kP111State81  = 81u' in block,
 'focus121':'kP111State121 = 121u' in block,
 'focus125':'kP111State125 = 125u' in block,
 'focus126':'kP111State126 = 126u' in block,
 'focus137':'kP111State137 = 137u' in block,
 'one_p111_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P111')==1,
 'no_p111_inline':'HOOK_DEFINE_INLINE(P111' not in cpp,
 'p110_runtime_absent':'[NSC:P110A]' not in cpp and 'P110CinematicManagerPhaseHook' not in cpp,
 'p109_runtime_absent':'[NSC:P109A]' not in cpp and 'P109State137ProvenanceHook' not in cpp,
 'p108_runtime_absent':'[NSC:P108A]' not in cpp and 'P108LifecycleStateBridgeHook' not in cpp,
 'p107_runtime_absent':'[NSC:P107A]' not in cpp and 'P107StateRequestBridgeHook' not in cpp,
 'p106_runtime_absent':'[NSC:P106A]' not in cpp and 'P106Controller520Hook' not in cpp,
 'p105_runtime_absent':'[NSC:P105B]' not in cpp and '[NSC:P105A]' not in cpp,
 'p104_runtime_absent':'[NSC:P104B]' not in cpp and '[NSC:P104A]' not in cpp,
 'p103_absent':'[NSC:P103A]' not in cpp,
 'p102_hold74_absent':'[NSC:P102A] HOLD74' not in cpp,
 'p101_hold125_absent':'P101State125GuardHook' not in cpp and '[NSC:P101A] HOLD125' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'slot_e28_logged':'slot_e28_off=0x%lx' in block and 'vtable + 0xE28' in block,
 'p110_retired':'p110_manager_retired=1' in block,
 'victim_action12_proof':'victim_action12_7de9b0_proven=1' in block,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_req_rewrite',not re.search(r'requested_state\s*=(?!=)|mapped_state|Orig\s*\([^\n]*kP111State',code_only))
chk('no_direct_state_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# Conservative logger bound (<512-byte LoggerMgr buffer).
def bounds(src):
 out=[]
 for m in re.finditer(r'Logging\.Log\((.*?)\);',src,re.S):
  expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
  if not lits: continue
  fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
  if '[NSC:P111A]' not in fmt: continue
  total=0; last=0
  for fm in re.finditer(r'%(?:0?8)?(?:l)?[uxp]',fmt):
   total+=len(fmt[last:fm.start()]); sp=fm.group(0)
   total+=10 if sp=='%u' else 8 if sp=='%08x' else 16 if sp=='%lx' else 18
   last=fm.end()
  total+=len(fmt[last:]); out.append((fmt.split()[1],total))
 return out
bds=bounds(block); print('p111_log_bounds',bds); chk('p111_log_buffer_guard',bool(bds) and all(n<512 for _,n in bds))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
b=paired.read_bytes(); assert b[:4]==b'NSO0'; flags=struct.unpack_from('<I',b,0x0C)[0]
tf,tm,ts=struct.unpack_from('<III',b,0x10); assert (flags&1)==0
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x7A89A4:0xA9BD5FFE,0x7A89A8:0xA90157F6,0x7A89AC:0xA9024FF4,0x7A89B0:0x2A0103F4,
 0x7A8A9C:0xB90E9C01,0x7A8AA0:0x52800028,0x7A8AA4:0x52800021,0x7A8AA8:0xB90EB008,
 0x7DE98C:0x1E2E1000,0x7DE990:0x52979D08,0x7DE994:0x12800002,0x7DE998:0xAA1303E0,
 0x7DE99C:0x52800181,0x7DE9A0:0x2A1F03E3,0x7DE9A4:0x2A1F03E4,0x7DE9A8:0x8B080274,
 0x7DE9AC:0x97FE2078,0x7DE9B0:0xAA1303E0,
 0x74F954:0xD10183FF,0x74F958:0xFD000BE8,0x74F95C:0xA90267FE,0x74F960:0xA9035FF8,
 0x74FF54:0xB9403260,0x74FF58:0x9404C05E,0x74FF60:0x94011909,0x74FF6C:0x52801121,
 0x74FF74:0xF946F908,0x74FF78:0xD63F0100,0x74FF7C:0xF94002E8,
}
for off,w in expected.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
# PlayAction12 call target proof.
def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
g=bl_target(0x7DE9AC); print('call',hex(0x7DE9AC),'->',hex(g)); assert g==0x766B8C
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p111a.yml']
print('P111A_DROPIN_SOURCE_VERIFY=PASS')
