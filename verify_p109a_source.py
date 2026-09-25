from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P109A — state137 request provenance probe')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P109State137ProvenanceHook)',start)
he=cpp.find('static bool InstallP109State137ProvenanceInternal()',hs)
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
 'entrypoint':'nsc::InstallP109State137ProvenanceProbe();' in main,
 'decl':'void InstallP109State137ProvenanceProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P109A] READY' in block,
 'state_req_log':'[NSC:P109A] STATE_REQ' in block,
 'state_request_offset':'kP109StateRequestOffset = 0x7A89A4' in block,
 'simple_setter_offset':'kP109SimpleE9CSetterOffset = 0x7A8A9C' in block,
 'focus125':'kP109State125 = 125u' in block,
 'focus136':'kP109State136 = 136u' in block,
 'focus137':'kP109State137 = 137u' in block,
 'one_p109_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P109')==1,
 'no_p109_inline':'HOOK_DEFINE_INLINE(P109' not in cpp,
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
 'p108_mapping_retired':'p108_mapping_retired=1' in block,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_req_rewrite',not re.search(r'requested_state\s*=(?!=)|mapped_state|Orig\s*\([^\n]*kP109State',code_only))
chk('no_direct_state_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# Conservative logger bound (<512 bytes LoggerMgr buffer).
def bounds(src):
 out=[]
 for m in re.finditer(r'Logging\.Log\((.*?)\);',src,re.S):
  expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
  if not lits: continue
  fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
  if '[NSC:P109A]' not in fmt: continue
  total=0; last=0
  for fm in re.finditer(r'%(?:0?8)?(?:l)?[uxp]',fmt):
   total+=len(fmt[last:fm.start()]); sp=fm.group(0)
   total+=10 if sp=='%u' else 8 if sp=='%08x' else 16 if sp=='%lx' else 18
   last=fm.end()
  total+=len(fmt[last:]); out.append((fmt.split()[1],total))
 return out
bds=bounds(block); print('p109_log_bounds',bds); chk('p109_log_buffer_guard',bool(bds) and all(n<512 for _,n in bds))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
b=paired.read_bytes(); assert b[:4]==b'NSO0'; flags=struct.unpack_from('<I',b,0x0C)[0]
tf,tm,ts=struct.unpack_from('<III',b,0x10); df,dm,ds=struct.unpack_from('<III',b,0x30)
assert (flags&1)==0
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x7A89A4:0xA9BD5FFE,0x7A89A8:0xA90157F6,0x7A89AC:0xA9024FF4,0x7A89B0:0x2A0103F4,
 0x7A89F0:0xB90E9E74,
 0x7A8A9C:0xB90E9C01,0x7A8AA0:0x52800028,0x7A8AA4:0x52800021,0x7A8AA8:0xB90EB008,
 0x7EB27C:0x52800FA1,0x7EB288:0xD63F0100,
 0x7A8310:0xB94E9675,0x7A834C:0x2A1F03E1,0x7A8350:0xD63F0100,
 0x7E47B8:0xF81A0FFD,0x7E4858:0x97FE08CD,
 0x7E64D4:0xD10683FF,0x7E6EA8:0x528058C1,0x7E6EC4:0x97FDFF32,
}
for off,w in expected.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
# Exact BL destinations remain PlayAction.
def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
for off in (0x7E4858,0x7E6EC4):
 g=bl_target(off); print('call',hex(off),'->',hex(g)); assert g==0x766B8C
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p109a.yml']
print('P109A_DROPIN_SOURCE_VERIFY=PASS')
