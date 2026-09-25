from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P113A — cinematic type10 session setup provenance')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P113ACinematicSessionSetupHook)',start)
he=cpp.find('static bool InstallP113ACinematicSessionSetupInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('outer_abi_u32_actor','static uint32_t Callback(void* actor)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'ReadActorIdentity(actor, side, cid)'))
chk('session_queries_before_orig',pos(h,'s10_pre = P113QuerySessionType(10)') < pos(h,'const uint32_t ret = Orig(actor);'))
chk('orig_exactly_once',len(re.findall(r'\bOrig\s*\(',h))==1)
chk('orig_unchanged','Orig(actor);' in h)
chk('post_queries_after_orig',pos(h,'const uint32_t ret = Orig(actor);') < pos(h,'s6_post = P113QuerySessionType(6)'))
checks={
 'entrypoint':'nsc::InstallP113ACinematicSessionSetupProbe();' in main,
 'decl':'void InstallP113ACinematicSessionSetupProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P113A] READY' in block,
 'session_log':'[NSC:P113A] SESSION' in block,
 'peer_log':'[NSC:P113A] PEER' in block,
 'outer_offset':'kP113SessionSetupOuterOffset = 0x7EF098' in block,
 'inner_offset':'kP113SessionSetupInnerOffset = 0x7EF128' in block,
 'query_offset':'kP113SessionQueryOffset = 0x750860' in block,
 'creator_offset':'kP113Type10CreatorOffset = 0x7514AC' in block,
 'creator_callsite':'kP113Type10CreatorCallsite = 0x7EF1B0' in block,
 'dispatch_offset':'kP113ManagerTypeDispatchOffset = 0x74F698' in block,
 'queries_6_9_10':all(f'P113QuerySessionType({x})' in h for x in (6,9,10)),
 'peer_vslot_dd0':'GetEventTargetActor(actor, 1)' in h,
 'e50_logged':'ReadActorI32At(actor, 0xE50)' in h,
 'one_p113_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P113')==1,
 'no_p113_inline':'HOOK_DEFINE_INLINE(P113' not in cpp,
 'p112_runtime_absent':'[NSC:P112B]' not in cpp and '[NSC:P112A]' not in cpp and 'P112BState125ProducerEntryHook' not in cpp,
 'p111_runtime_absent':'[NSC:P111A]' not in cpp and 'P111VictimStateProvenanceHook' not in cpp,
 'p110_runtime_absent':'[NSC:P110A]' not in cpp and 'P110CinematicManagerPhaseHook' not in cpp,
 'p109_runtime_absent':'[NSC:P109A]' not in cpp and 'P109State137ProvenanceHook' not in cpp,
 'p108_runtime_absent':'[NSC:P108A]' not in cpp and 'P108LifecycleStateBridgeHook' not in cpp,
 'p107_runtime_absent':'[NSC:P107A]' not in cpp and 'P107StateRequestBridgeHook' not in cpp,
 'p106_runtime_absent':'[NSC:P106A]' not in cpp and 'P106Controller520Hook' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_manual_session_claim':'no_manual_session_create=1' in block,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_state_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# No call to creator or inserter from diagnostic code; only offsets/fingerprints are allowed.
chk('no_manual_type10_creator_call','reinterpret_cast' not in block[block.find('kP113Type10CreatorOffset'):block.find('kP113Type10CreatorOffset')+250])
# conservative LoggerMgr 512-byte bound
out=[]
for m in re.finditer(r'Logging\.Log\((.*?)\);',block,re.S):
 expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
 if not lits: continue
 fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
 if '[NSC:P113A]' not in fmt: continue
 total=0; last=0
 for fm in re.finditer(r'%(?:0?8)?(?:l)?[duxp]',fmt):
  total+=len(fmt[last:fm.start()]); sp=fm.group(0)
  if sp in ('%u','%d'): total+=11
  elif sp=='%08x': total+=8
  elif sp=='%lx': total+=16
  elif sp=='%p': total+=18
  last=fm.end()
 total+=len(fmt[last:]); out.append((fmt.split()[1],total))
print('p113_log_bounds',out); chk('p113_log_buffer_guard',bool(out) and all(n<512 for _,n in out))
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
 0x7EF098:0xF81E0FFE,0x7EF09C:0xA9014FF4,0x7EF0A0:0xAA0003F3,0x7EF0A4:0x940023EE,
 0x7EF100:0x97FFCCE4,0x7EF104:0xAA1303E0,0x7EF108:0x94000008,0x7EF10C:0x34000080,
 0x7EF128:0xA9BE57FE,0x7EF12C:0xA9014FF4,0x7EF130:0xF9400008,0x7EF134:0xAA0003F3,
 0x7EF150:0x52800120,0x7EF154:0x97FD85C3,0x7EF158:0x35000080,0x7EF15C:0x528000C0,0x7EF160:0x97FD85C0,0x7EF164:0x340000C0,
 0x7EF17C:0xAA1303E0,0x7EF180:0x97FE9C81,0x7EF184:0xB40001A0,0x7EF188:0xB94E5274,
 0x7EF190:0x97FE9C7D,0x7EF194:0xF9465C09,0x7EF1A0:0xF9400D29,0x7EF1A4:0xD63F0120,
 0x7EF1A8:0x2A0003E1,0x7EF1AC:0x2A1403E0,0x7EF1B0:0x97FD88BF,
 0x7514AC:0xA9BF4FFE,0x7514C8:0x52800141,0x7514D0:0x97FFFDEA,0x7514D8:0xB9003413,
 0x750860:0xB000CFE8,0x750888:0xB9403D2A,0x750894:0xB940392A,0x75089C:0x52800020,
 0x74F698:0xB9403E88,0x74F69C:0x7100291F,0x74F6AC:0x940000AA,
}
for off,w in expected.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w

def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
for off,target in [(0x7EF100,0x7E2490),(0x7EF108,0x7EF128),(0x7EF154,0x750860),(0x7EF160,0x750860),(0x7EF180,0x796384),(0x7EF190,0x796384),(0x7EF1B0,0x7514AC),(0x7514D0,0x750C78),(0x74F6AC,0x74F954)]:
 g=bl_target(off); print('call',hex(off),'->',hex(g)); assert g==target
# type10 creator is uniquely reached by direct BL at 0x7EF1B0
hits=[]
for off in range(0,len(text)-4,4):
 w=word(off)
 if (w>>26)!=0b100101: continue
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 if off+(imm<<2)==0x7514AC: hits.append(off)
print('type10_creator_direct_callers',[hex(x) for x in hits]); chk('unique_type10_creator_caller',hits==[0x7EF1B0])
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 ss=p.read_text()
 if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p113a.yml']
print('P113A_DROPIN_SOURCE_VERIFY=PASS')
