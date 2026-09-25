from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P106A — +0x520 entry proof')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P106Controller520Hook)',start)
he=cpp.find('static bool InstallP106Controller520EntryProofInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('520_void_abi','static void Callback(void* actor, uint32_t mode)' in h)
chk('520_caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('520_orig_paths',len(re.findall(r'^\s*Orig\(actor, mode\);\s*$',h,re.M))==2)
chk('520_player_filter','side == 0u' in h)
chk('520_pre_before_orig',pos(h,'const P93CoreState pre = ReadP93CoreState(actor);') < h.rfind('Orig(actor, mode);'))
chk('520_post_after_orig',h.rfind('Orig(actor, mode);') < pos(h,'const P93CoreState post = ReadP93CoreState(actor);'))
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
checks={
 'entrypoint':'nsc::InstallP106Controller520EntryProof();' in main,
 'decl':'void InstallP106Controller520EntryProof();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P106A] READY' in block,
 'ctrl520_log':'[NSC:P106A] CTRL520' in block,
 'state520_log':'[NSC:P106A] STATE520' in block,
 'offset_520':'kP106Controller520Offset = 0x7E64D4' in block,
 'one_p106_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P106Controller')==1,
 'no_p106_inline':'HOOK_DEFINE_INLINE(P106' not in cpp,
 'no_4c0_p106_hook':'P106Controller4C0Hook' not in cpp,
 'focused_700_711':'st.action >= 700u && st.action <= 711u' in block,
 'logs_mode':'mode=%u' in block,
 'logs_caller':'caller_off=0x%lx' in block and 'callsite_off=0x%lx' in block,
 'logs_vslots':'slot4c0_off=0x%lx' in block and 'slot520_off=0x%lx' in block,
 'p105b_runtime_absent':'[NSC:P105B]' not in cpp and 'P105BController4C0Hook' not in cpp,
 'p105a_runtime_absent':'[NSC:P105A]' not in cpp,
 'p104_runtime_absent':'[NSC:P104B]' not in cpp and '[NSC:P104A]' not in cpp,
 'p103_absent':'[NSC:P103A]' not in cpp and 'P103SpecialCondFactoryBridgeHook' not in cpp,
 'p102_absent':'[NSC:P102A] HOLD74' not in cpp,
 'p101_absent':'P101State125GuardHook' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',block),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',block),
 'no_mode_assignment':not re.search(r'\bmode\s*=(?!=)',code_only),
 'no_actor_state_write':not re.search(r'reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only),
 'no_char281_branch':not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',block),
}
for k,v in checks.items(): chk(k,v)
# conservative log size guard (<512-byte logger buffer)
def bounds(src):
 out=[]
 for m in re.finditer(r'Logging\.Log\((.*?)\);',src,re.S):
  expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
  if not lits: continue
  fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
  if '[NSC:P106A]' not in fmt: continue
  total=0; last=0
  for fm in re.finditer(r'%(?:0?8)?(?:l)?[uxp]',fmt):
   total+=len(fmt[last:fm.start()]); sp=fm.group(0)
   total+=10 if sp=='%u' else 8 if sp=='%08x' else 16 if sp=='%lx' else 18
   last=fm.end()
  total+=len(fmt[last:]); out.append((fmt.split()[1],total))
 return out
bds=bounds(block); print('p106_log_bounds',bds); chk('p106_log_buffer_guard',bool(bds) and all(n<512 for _,n in bds))
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
 0x7E64D4:0xD10683FF,0x7E64D8:0xA9147BFD,0x7E64DC:0xA9156FFC,0x7E64E0:0xA91667FA,
 0x7E64E4:0xA9175FF8,0x7E64E8:0xA91857F6,0x7E64EC:0xA9194FF4,
 0x7E6EA8:0x528058C1,0x7E6EC4:0x97FDFF32,0x488B28:0x940D766B,
 0x7DDD94:0xD10243FF,
}
for off,w in expected.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
for off,tgt in [(0x7E6EC4,0x766B8C),(0x488B28,0x7E64D4)]:
 g=bl_target(off); print('call',hex(off),'->',hex(g)); assert g==tgt
refs=[]
for off in range(0,len(text)-4,4):
 w=word(off)
 if (w>>26)!=0b100101: continue
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 if off+(imm<<2)==0x7E64D4: refs.append(off)
print('direct_bl_520',[hex(x) for x in refs]); assert refs==[0x488B28]
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p106a.yml']
print('P106A_DROPIN_SOURCE_VERIFY=PASS')
