from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P116A — universal cinematic outer-caller census')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P116ACinematicOuterCallerCensusHook)',start)
he=cpp.find('static bool InstallP116ACinematicOuterCallerCensusInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('outer_abi_u32_actor','static uint32_t Callback(void* actor)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('orig_exactly_once',len(re.findall(r'\bOrig\s*\(',h))==1)
chk('orig_unchanged','Orig(actor);' in h)
chk('pre_queries_before_orig',pos(h,'s10_pre = P116QuerySessionType(10)') < pos(h,'const uint32_t ret = Orig(actor);'))
chk('post_queries_after_orig',pos(h,'const uint32_t ret = Orig(actor);') < pos(h,'s9_post = P116QuerySessionType(9)'))
checks={
 'entrypoint':'nsc::InstallP116ACinematicOuterCallerCensusProbe();' in main,
 'decl':'void InstallP116ACinematicOuterCallerCensusProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P116A] READY' in block,
 'call_log':'[NSC:P116A] CALL' in block,
 'peer_log':'[NSC:P116A] PEER' in block,
 'outer_offset':'kP116SessionSetupOuterOffset = 0x7EF098' in block,
 'query_offset':'kP116SessionQueryOffset = 0x750860' in block,
 'creator_offset':'kP116Type10CreatorOffset = 0x7514AC' in block,
 'creator_callsite':'kP116Type10CreatorCallsite = 0x7EF1B0' in block,
 'six_buckets':all(x in block for x in ['0x0D6BE0','0x0FBF64','0x32F574','0x753CBC','0x77C5EC','0x802638']),
 'queries_9_10':all(f'P116QuerySessionType({x})' in h for x in (9,10)),
 'peer_vslot_dd0':'GetEventTargetActor(actor, 1)' in h,
 'one_p116_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P116')==1,
 'no_p116_inline':'HOOK_DEFINE_INLINE(P116' not in cpp,
 'p115_runtime_absent':'[NSC:P115' not in cpp and 'P115' not in main,
 'p114_runtime_absent':'[NSC:P114A]' not in cpp,
 'p113_runtime_absent':'[NSC:P113A]' not in cpp and 'P113ACinematicSessionSetupHook' not in cpp,
 'p112_runtime_absent':'[NSC:P112B]' not in cpp and '[NSC:P112A]' not in cpp,
 'p111_runtime_absent':'[NSC:P111A]' not in cpp,
 'p110_runtime_absent':'[NSC:P110A]' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_manual_session_claim':'no_manual_session_create=1' in block,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_state_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# conservative LoggerMgr 512-byte bound
out=[]
for m in re.finditer(r'Logging\.Log\((.*?)\);',block,re.S):
 expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
 if not lits: continue
 fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
 if '[NSC:P116A]' not in fmt: continue
 total=0; last=0
 for fm in re.finditer(r'%(?:0?8)?(?:l)?[duxp]',fmt):
  total+=len(fmt[last:fm.start()]); sp=fm.group(0)
  if sp in ('%u','%d'): total+=11
  elif sp=='%08x': total+=8
  elif sp=='%lx': total+=16
  elif sp=='%p': total+=18
  last=fm.end()
 total+=len(fmt[last:]); out.append((fmt.split()[1],total))
print('p116_log_bounds',out); chk('p116_log_buffer_guard',bool(out) and all(n<512 for _,n in out))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
b=paired.read_bytes(); assert b[:4]==b'NSO0'; flags=struct.unpack_from('<I',b,0x0C)[0]
tf,tm,ts=struct.unpack_from('<III',b,0x10); assert (flags&1)==0
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
# exact outer signature
for off,w in {0x7EF098:0xF81E0FFE,0x7EF09C:0xA9014FF4,0x7EF0A0:0xAA0003F3,0x7EF0A4:0x940023EE}.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
# scan every direct BL to outer setup and require the complete six-caller set
hits=[]
for off in range(0,len(text)-4,4):
 w=word(off)
 if (w>>26)!=0b100101: continue
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 if off+(imm<<2)==0x7EF098: hits.append(off)
expected_callers=[0x0D6BDC,0x0FBF60,0x32F570,0x753CB8,0x77C5E8,0x802634]
print('outer_direct_callsites',[hex(x) for x in hits]); chk('six_outer_direct_callers',hits==expected_callers)
for off in expected_callers:
 print('call',hex(off),'->',hex(bl_target(off))); assert bl_target(off)==0x7EF098
# type10 creator still has exactly one direct caller inside the outer/inner setup path
creator_hits=[]
for off in range(0,len(text)-4,4):
 w=word(off)
 if (w>>26)!=0b100101: continue
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 if off+(imm<<2)==0x7514AC: creator_hits.append(off)
print('type10_creator_direct_callers',[hex(x) for x in creator_hits]); chk('unique_type10_creator_caller',creator_hits==[0x7EF1B0])
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 ss=p.read_text()
 if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p116a.yml']
print('P116A_DROPIN_SOURCE_VERIFY=PASS')
