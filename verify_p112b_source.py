from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P112B — exact state125 producer entry provenance')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P112BState125ProducerEntryHook)',start)
he=cpp.find('static bool InstallP112BState125ProducerEntryInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('producer_abi_void_actor','static void Callback(void* actor)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('peer_after_caller',pos(h,'ReadActorIdentity(actor, side, cid)') < pos(h,'GetEventTargetActor(actor, 1)'))
chk('orig_exactly_once',len(re.findall(r'\bOrig\s*\(',h))==1)
chk('orig_unchanged','Orig(actor);' in h)
chk('post_after_orig',pos(h,'Orig(actor);') < pos(h,'const P93CoreState post ='))
checks={
 'entrypoint':'nsc::InstallP112BState125ProducerEntryProbe();' in main,
 'decl':'void InstallP112BState125ProducerEntryProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P112B] READY' in block,
 'entry_log':'[NSC:P112B] ENTRY' in block,
 'producer_offset':'kP112State125ProducerOffset = 0x7EB270' in block,
 'request_offset':'kP112StateRequestOffset = 0x7A89A4' in block,
 'victim126_landmark':'kP112Victim126CallerReturn = 0x7DDFE4' in block,
 'victim12_landmark':'kP112VictimAction12Return = 0x7DE9B0' in block,
 'peer_vslot_dd0':'GetEventTargetActor(actor, 1)' in block,
 'one_p112_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P112')==1,
 'no_p112_inline':'HOOK_DEFINE_INLINE(P112' not in cpp,
 'p111_runtime_absent':'[NSC:P111A]' not in cpp and 'P111VictimStateProvenanceHook' not in cpp,
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
 'p111_retired':'p111_gateway_retired=1' in block,
 'no_manual_call_claim':'no_manual_producer_call=1' in block,
}
for k,v in checks.items(): chk(k,v)
chk('victim126_runtime_sig_source', 'static constexpr uint32_t sigVictim126[] = {\n        0xF9400268, 0xAA1303E0, 0x52800FC1, 0xF946F908, 0xD63F0100,' in block)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_state_map',not re.search(r'mapped_state|requested_state\s*=|req\s*=\s*(?:39|81|121|125|126|137)',code_only))
chk('no_direct_state_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# The producer must only be installed as a hook, never called by absolute address.
chk('no_manual_producer_call',block.count('kP112State125ProducerOffset')==4 and 'reinterpret_cast' not in block[block.find('kP112State125ProducerOffset'):block.find('kP112State125ProducerOffset')+300])
# Conservative logger bound (<512-byte LoggerMgr buffer).
def bounds(src):
 out=[]
 for m in re.finditer(r'Logging\.Log\((.*?)\);',src,re.S):
  expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
  if not lits: continue
  fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
  if '[NSC:P112B]' not in fmt: continue
  total=0; last=0
  for fm in re.finditer(r'%(?:0?8)?(?:l)?[uxp]',fmt):
   total+=len(fmt[last:fm.start()]); sp=fm.group(0)
   total+=10 if sp=='%u' else 8 if sp=='%08x' else 16 if sp=='%lx' else 18
   last=fm.end()
  total+=len(fmt[last:]); out.append((fmt.split()[1],total))
 return out
bds=bounds(block); print('p112_log_bounds',bds); chk('p112_log_buffer_guard',bool(bds) and all(n<512 for _,n in bds))
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
 0x7EB270:0xF81E0FFE,0x7EB274:0xA9014FF4,0x7EB278:0xF9400008,0x7EB27C:0x52800FA1,
 0x7EB280:0xAA0003F3,0x7EB284:0xF946F908,0x7EB288:0xD63F0100,0x7EB28C:0xF9400268,
 0x7A89A4:0xA9BD5FFE,0x7A89A8:0xA90157F6,0x7A89AC:0xA9024FF4,0x7A89B0:0x2A0103F4,
 0x7DDFD0:0xF9400268,0x7DDFD4:0xAA1303E0,0x7DDFD8:0x52800FC1,0x7DDFDC:0xF946F908,
 0x7DDFE0:0xD63F0100,0x7DDFE4:0xF9400268,
 0x7DE98C:0x1E2E1000,0x7DE990:0x52979D08,0x7DE994:0x12800002,0x7DE998:0xAA1303E0,
 0x7DE99C:0x52800181,0x7DE9A0:0x2A1F03E3,0x7DE9A4:0x2A1F03E4,0x7DE9A8:0x8B080274,
 0x7DE9AC:0x97FE2078,0x7DE9B0:0xAA1303E0,
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
print('push_enabled_workflows',push); assert push==['build-subsdk9-p112b.yml']
print('P112B_DROPIN_SOURCE_VERIFY=PASS')
