from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P110A — type10 UJ/cinematic manager phase provenance probe')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P110CinematicManagerPhaseHook)',start)
he=cpp.find('static bool InstallP110CinematicManagerPhaseInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('manager_abi','static uint32_t Callback(void* manager, void* ctx)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'P110ReadManagerState(ctx)'))
chk('unexpected_passthrough', 'return Orig(manager, ctx);' in h)
chk('orig_two_textual_paths',len(re.findall(r'\bOrig\s*\(',h))==2)
chk('focused_orig_unchanged','const uint32_t ret = Orig(manager, ctx);' in h)
chk('post_after_orig',pos(h,'const uint32_t ret = Orig(') < pos(h,'const P110ManagerState post ='))
checks={
 'entrypoint':'nsc::InstallP110CinematicManagerPhaseProbe();' in main,
 'decl':'void InstallP110CinematicManagerPhaseProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P110A] READY' in block,
 'mgr_log':'[NSC:P110A] MGR' in block,
 'leader_log':'[NSC:P110A] LEADER' in block,
 'paired_log':'[NSC:P110A] PAIRED' in block,
 'manager_offset':'kP110ManagerOffset = 0x74F954' in block,
 'caller_return':'kP110ManagerCallerReturn = 0x74F6B0' in block,
 'resolve_actor':'kP110ResolveActorOffset = 0x8800D0' in block,
 'paired_actor':'kP110PairedActorOffset = 0x796384' in block,
 'b968_read':'b + 0xB968' in block,
 'one_p110_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P110')==1,
 'no_p110_inline':'HOOK_DEFINE_INLINE(P110' not in cpp,
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
 'p109_retired':'p109_retired=1' in block,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_actor_state_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|leader_cid|paired_cid)\s*==\s*281|281\s*==\s*(?:char_id|cid|leader_cid|paired_cid)',code_only))
# Logger conservative bounds (<512-byte LoggerMgr buffer).
def bounds(src):
 out=[]
 for m in re.finditer(r'Logging\.Log\((.*?)\);',src,re.S):
  expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
  if not lits: continue
  fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
  if '[NSC:P110A]' not in fmt: continue
  total=0; last=0
  for fm in re.finditer(r'%(?:0?8)?(?:l)?[udxp]',fmt):
   total+=len(fmt[last:fm.start()]); sp=fm.group(0)
   total += 10 if sp=='%u' else 11 if sp=='%d' else 8 if sp=='%08x' else 16 if sp=='%lx' else 18
   last=fm.end()
  total+=len(fmt[last:]); out.append((fmt.split()[1],total))
 return out
bds=bounds(block); print('p110_log_bounds',bds); chk('p110_log_buffer_guard',bool(bds) and all(n<512 for _,n in bds))
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
 0x74F954:0xD10183FF,0x74F958:0xFD000BE8,0x74F95C:0xA90267FE,0x74F960:0xA9035FF8,
 0x74F964:0xA90457F6,0x74F968:0xA9054FF4,0x74F96C:0xAA0003F6,0x74F970:0xB9403020,
 0x74F698:0xB9403E88,0x74F69C:0x7100291F,0x74F6A0:0x540002C1,0x74F6A4:0x91004281,
 0x74F6A8:0xAA1303E0,0x74F6AC:0x940000AA,0x74F6B0:0x34000240,
 0x74FA9C:0xAA1503E0,0x74FAA0:0x94011A39,0x74FAA4:0xB4000080,0x74FAA8:0x94011C51,
 0x74FAAC:0x7100041F,0x74FAB0:0x5400340C,0x74FABC:0x52800069,
 0x74FF54:0xB9403260,0x74FF58:0x9404C05E,0x74FF60:0x94011909,0x74FF6C:0x52801121,
 0x74FF74:0xF946F908,0x74FF78:0xD63F0100,0x74FF7C:0xF94002E8,
 0x796BEC:0x52972D08,0x796BF0:0xF8686808,0x796BF4:0xB4000068,0x796BF8:0xB9400100,
 0x796BFC:0xD65F03C0,0x796C00:0x2A1F03E0,0x796C04:0xD65F03C0,
}
for off,w in expected.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
# BL decoder and uniqueness proofs.
def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
for off,tgt in [(0x74F6AC,0x74F954),(0x74FAA0,0x796384),(0x74FAA8,0x796BEC)]:
 g=bl_target(off); print('call',hex(off),'->',hex(g)); assert g==tgt
refs=[]
for off in range(0,len(text)-4,4):
 w=word(off)
 if (w>>26)==0b100101 and bl_target(off)==0x74F954: refs.append(off)
print('direct_bl_manager',[hex(x) for x in refs]); assert refs==[0x74F6AC]
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p110a.yml']
print('P110A_DROPIN_SOURCE_VERIFY=PASS')
