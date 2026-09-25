from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P108A — exact post-708 lifecycle-state restoration')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P108LifecycleStateBridgeHook)',start)
he=cpp.find('static bool InstallP108LifecycleStateBridgeInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('state_req_abi','static uint32_t Callback(void* actor, uint32_t requested_state' in h and 'uint32_t arg2, uint32_t arg3)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('fast_filter_before_actor',pos(h,'if (caller_off != kP108CleanupCallerReturn || requested_state != kP108CleanupState)') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('orig_two_exclusive_paths',len(re.findall(r'\bOrig\s*\(',h))==2)
chk('fast_passthrough','return Orig(actor, requested_state, arg2, arg3);' in h)
chk('mapped_orig_once','const uint32_t ret = Orig(actor, mapped_state, arg2, arg3);' in h)
chk('post_after_orig',pos(h,'const uint32_t ret = Orig(') < pos(h,'const P93CoreState post ='))
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
checks={
 'entrypoint':'nsc::InstallP108Post708LifecycleBridge();' in main,
 'decl':'void InstallP108Post708LifecycleBridge();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P108A] READY' in block,
 'bridge_log':'[NSC:P108A] BRIDGE' in block,
 'state_request_offset':'kP108StateRequestOffset = 0x7A89A4' in block,
 'cleanup_caller':'kP108CleanupCallerReturn = 0x7EB28C' in block,
 'cleanup_125':'kP108CleanupState = 125u' in block,
 'setup_136':'kP108SetupState = 136u' in block,
 'no_map137':'kP108SetupState = 137u' not in block,
 'one_p108_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P108')==1,
 'no_p108_inline':'HOOK_DEFINE_INLINE(P108' not in cpp,
 'exact_args':'arg2 == 1u && arg3 == 0u' in block,
 'exact_action708':'pre.action == 708u' in block,
 'exact_prestate':'pre.e94 == 63u && pre.e98 == 136u && pre.e9c == 0u' in block,
 'exact_controlstate':'pre.bda4 == 1u && pre.bda8 == 0u && pre.bdc8 == 0u' in block,
 'semantic_gate':'P64QuerySemanticUltimateJutsu(actor)' in block,
 'membership_gate':'p81_data::ContainsOugiAwakeningId(cid)' in block,
 'player_side_only':'side == 0u' in block,
 'p107_runtime_absent':'[NSC:P107A]' not in cpp and 'P107StateRequestBridgeHook' not in cpp,
 'p106_runtime_absent':'[NSC:P106A]' not in cpp and 'P106Controller520Hook' not in cpp,
 'p105_runtime_absent':'[NSC:P105B]' not in cpp and '[NSC:P105A]' not in cpp,
 'p104_runtime_absent':'[NSC:P104B]' not in cpp and '[NSC:P104A]' not in cpp,
 'p103_absent':'[NSC:P103A]' not in cpp,
 'p102_hold74_absent':'[NSC:P102A] HOLD74' not in cpp,
 'p101_hold125_absent':'P101State125GuardHook' not in cpp and '[NSC:P101A] HOLD125' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',block),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',block),
 'no_direct_state_write':not re.search(r'reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only),
 'no_char281_branch':not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',block),
 'return_native_ret':'return ret;' in h,
 'ctrl518_guard':'MatchWords(0x7E47B8, sigController518)' in block,
 'ctrl520_guard':'MatchWords(0x7E64D4, sigController520)' in block,
 'participant136_guard':'MatchWords(0x7E54A0, sigController518Participant136)' in block,
 'participant138_guard':'MatchWords(0x7E5504, sigController518Participant138)' in block,
 'participant137_guard':'MatchWords(0x7E5570, sigController518Participant137)' in block,
}
for k,v in checks.items(): chk(k,v)
# Conservative P108 logger bound; LoggerMgr buffer is 512 bytes.
def bounds(src):
 out=[]
 for m in re.finditer(r'Logging\.Log\((.*?)\);',src,re.S):
  expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
  if not lits: continue
  fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
  if '[NSC:P108A]' not in fmt: continue
  total=0; last=0
  for fm in re.finditer(r'%(?:0?8)?(?:l)?[uxp]',fmt):
   total+=len(fmt[last:fm.start()]); sp=fm.group(0)
   total+=10 if sp=='%u' else 8 if sp=='%08x' else 16 if sp=='%lx' else 18
   last=fm.end()
  total+=len(fmt[last:]); out.append((fmt.split()[1],total))
 return out
bds=bounds(block); print('p108_log_bounds',bds); chk('p108_log_buffer_guard',bool(bds) and all(n<512 for _,n in bds))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]
tf,tm,ts=struct.unpack_from('<III',b,0x10)
rf,rm,rs=struct.unpack_from('<III',b,0x20)
df,dm,ds=struct.unpack_from('<III',b,0x30)
assert (flags&1)==0
text=b[tf:tf+ts]
data=b[df:df+ds]
def word(off): return struct.unpack_from('<I',text,off)[0]
def data_q(addr):
 assert dm<=addr<=dm+ds-8
 return struct.unpack_from('<Q',data,addr-dm)[0]
expected={
 0x7A89A4:0xA9BD5FFE,0x7A89A8:0xA90157F6,0x7A89AC:0xA9024FF4,0x7A89B0:0x2A0103F4,
 0x7A89B4:0xAA0003F3,0x7A89B8:0x34000282,0x7A89BC:0xF9400268,0x7A89C0:0xAA1303E0,
 0x7EB270:0xF81E0FFE,0x7EB274:0xA9014FF4,0x7EB278:0xF9400008,0x7EB27C:0x52800FA1,
 0x7EB280:0xAA0003F3,0x7EB284:0xF946F908,0x7EB288:0xD63F0100,0x7EB28C:0xF9400268,
 0x7A8310:0xB94E9675,0x7A834C:0x2A1F03E1,0x7A8350:0xD63F0100,
 0x7E47B8:0xF81A0FFD,0x7E47BC:0xA9016FFE,0x7E4828:0x52805894,
 0x7E54A0:0x52801101,0x7E54B0:0x97FE05B7,0x7E5504:0x52801141,0x7E5570:0x52801121,
 0x7E64D4:0xD10683FF,0x7E6EA8:0x528058C1,0x7E6EC4:0x97FDFF32,
}
for off,w in expected.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
# Exact cleanup producer encodes state125.
w=word(0x7EB27C); imm16=(w>>5)&0xFFFF; print('cleanup_mov_state',imm16); assert imm16==125
# State record table proof. Table base was resolved from relocation target at main+0x214D248.
state_table=0x205AAF8
records={125:(0x4C0,1,0,0x10),136:(0x518,1,0,0x7),137:(0x520,1,0,0xF)}
for st,expect in records.items():
 vals=tuple(data_q(state_table+st*0x20+i*8) for i in range(4))
 print('state_record',st,tuple(hex(x) for x in vals)); assert vals==expect
# Native 710 call still targets PlayAction.
def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
for off,tgt in [(0x7E54B0,0x766B8C),(0x7E6EC4,0x766B8C)]:
 g=bl_target(off); print('call',hex(off),'->',hex(g)); assert g==tgt
# Pure-Python LZ4 block decompressor to independently resolve the relevant RELA entries.
def lz4_block(src, out_size):
 out=bytearray(); i=0
 while i < len(src):
  token=src[i]; i+=1
  lit=token>>4
  if lit==15:
   while True:
    x=src[i]; i+=1; lit+=x
    if x!=255: break
  out+=src[i:i+lit]; i+=lit
  if i>=len(src): break
  off=src[i] | (src[i+1]<<8); i+=2
  assert off and off<=len(out)
  ml=(token&15)+4
  if (token&15)==15:
   while True:
    x=src[i]; i+=1; ml+=x
    if x!=255: break
  for _ in range(ml): out.append(out[-off])
 assert len(out)==out_size,(len(out),out_size)
 return bytes(out)
ro_comp_size=struct.unpack_from('<I',b,0x64)[0]
ro=lz4_block(b[rf:rf+ro_comp_size],rs) if flags&2 else b[rf:rf+rs]
def mem(addr,n):
 if tm<=addr<tm+ts: return text[addr-tm:addr-tm+n]
 if rm<=addr<rm+rs: return ro[addr-rm:addr-rm+n]
 if dm<=addr<dm+ds: return data[addr-dm:addr-dm+n]
 raise AssertionError(hex(addr))
dyn_rel=struct.unpack_from('<I',text,12)[0]
dyn=8+dyn_rel
dtags={}
for i in range(128):
 tag,val=struct.unpack('<QQ',mem(dyn+i*16,16)); dtags.setdefault(tag,[]).append(val)
 if tag==0: break
rela=dtags[7][0]; relasz=dtags[8][0]; relaent=dtags[9][0]
want={0x214D248:0x205AAF8,
      0x201BF58+0x4C0:0x7DDD94,
      0x201BF58+0x518:0x7E47B8,
      0x201BF58+0x520:0x7E64D4}
found={}
for i in range(relasz//relaent):
 roff,rinfo,radd=struct.unpack('<QQq',mem(rela+i*relaent,24))
 if roff in want: found[roff]=(rinfo,radd)
assert set(found)==set(want),(found,want)
for roff,add in want.items():
 info,radd=found[roff]
 print('rela',hex(roff),'type',info&0xffffffff,'addend',hex(radd))
 assert (info&0xffffffff)==1027 and radd==add
print('state_table_and_vslots PASS')
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p108a.yml']
print('P108A_DROPIN_SOURCE_VERIFY=PASS')
