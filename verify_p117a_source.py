from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P117A — action-event stream census')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P117AActionEventStreamCensusHook)',start)
he=cpp.find('static bool InstallP117AActionEventStreamCensusInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('hook_abi_u32_event_x0','static uint32_t Callback(void* event_x0)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'if (caller_off != kP117FocusedCallerReturn)'))
chk('fast_passthrough_before_event_reads',pos(h,'if (caller_off != kP117FocusedCallerReturn)') < pos(h,'payload28 = *reinterpret_cast'))
chk('orig_two_textual_paths',len(re.findall(r'\bOrig\s*\(',h))==2)
chk('fast_orig_unchanged','return Orig(event_x0);' in h)
chk('focused_orig_unchanged','const uint32_t ret = Orig(event_x0);' in h)
chk('event_reads_before_focused_orig',pos(h,'raw_type = *reinterpret_cast') < pos(h,'const uint32_t ret = Orig(event_x0);'))
checks={
 'entrypoint':'nsc::InstallP117AActionEventStreamCensusProbe();' in main,
 'decl':'void InstallP117AActionEventStreamCensusProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P117A] READY' in block,
 'event_log':'[NSC:P117A] EVENT' in block,
 'getter_offset':'kP117EventGateGetterOffset = 0x3F4BC0' in block,
 'focused_return':'kP117FocusedCallerReturn = 0x77B5AC' in block,
 'dispatcher_offset':'kP117DispatcherEntryOffset = 0x77B560' in block,
 'lookup_callsite':'kP117EventLookupCallsite = 0x77B590' in block,
 'gate_callsite':'kP117GateGetterCallsite = 0x77B5A8' in block,
 'type_gate_offset':'kP117Type10GateOffset = 0x77C474' in block,
 'outer_callsite':'kP117OuterCallsite = 0x77C5E8' in block,
 'event_type_fields':all(x in h for x in ['b + 0x28','b + 0x48','b + 0x50']),
 'type10_normalization':'raw_type & 0xFFFFFFFEu' in h and 'norm_type == 10u' in h,
 'one_p117_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P117')==1,
 'no_p117_inline':'HOOK_DEFINE_INLINE(P117' not in cpp,
 'p116_runtime_absent':'[NSC:P116A]' not in cpp and 'P116' not in main,
 'p115_runtime_absent':'[NSC:P115' not in cpp,
 'p114_runtime_absent':'[NSC:P114A]' not in cpp,
 'p113_runtime_absent':'[NSC:P113A]' not in cpp,
 'p112_runtime_absent':'[NSC:P112B]' not in cpp and '[NSC:P112A]' not in cpp,
 'p111_runtime_absent':'[NSC:P111A]' not in cpp,
 'p110_runtime_absent':'[NSC:P110A]' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_state_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_branch_patch','WriteInst' not in block and 'Patch' not in code_only)
chk('no_session_create','0x7514AC' not in block and '0x750C78' not in block)
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# conservative LoggerMgr 512-byte bound
out=[]
for m in re.finditer(r'Logging\.Log\((.*?)\);',block,re.S):
 expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
 if not lits: continue
 fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
 if '[NSC:P117A]' not in fmt: continue
 total=0; last=0
 for fm in re.finditer(r'%(?:0?8)?(?:l)?[duxp]',fmt):
  total+=len(fmt[last:fm.start()]); sp=fm.group(0)
  if sp in ('%u','%d'): total+=11
  elif sp=='%08x': total+=8
  elif sp=='%lx': total+=16
  elif sp=='%p': total+=18
  last=fm.end()
 total+=len(fmt[last:]); out.append((fmt.split()[1],total))
print('p117_log_bounds',out); chk('p117_log_buffer_guard',bool(out) and all(n<512 for _,n in out))
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
for off,w in {
 0x3F4BC0:0xF000EA68,0x3F4BC4:0xF9424508,0x3F4BC8:0xF9760908,
 0x3F4BCC:0xF9405D08,0x3F4BD0:0x79415100,0x3F4BD4:0xD65F03C0,
 0x77B560:0xFC180FEA,0x77B584:0x52973C88,0x77B590:0x97F1E55C,
 0x77B5A4:0xAA0003F4,0x77B5A8:0x97F1E586,0x77B5AC:0x6B2022BF,
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,
 0x77C480:0x54000B81,0x77C5E8:0x9401CAAC,
}.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
print('bl 0x77b590 ->',hex(bl_target(0x77B590))); assert bl_target(0x77B590)==0x3F4B00
print('bl 0x77b5a8 ->',hex(bl_target(0x77B5A8))); assert bl_target(0x77B5A8)==0x3F4BC0
print('bl 0x77c5e8 ->',hex(bl_target(0x77C5E8))); assert bl_target(0x77C5E8)==0x7EF098
# prove getter has seven direct callers and focus return is one of them
hits=[]
for off in range(0,len(text)-4,4):
 w=word(off)
 if (w>>26)!=0b100101: continue
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 if off+(imm<<2)==0x3F4BC0: hits.append(off)
expected=[0x0D5FB0,0x0FB408,0x3019D8,0x32E6BC,0x77B5A8,0x77D29C,0x77D640]
print('getter_direct_callsites',[hex(x) for x in hits]); chk('seven_getter_direct_callers',hits==expected)
# dispatcher itself has one direct caller in paired main
hits2=[]
for off in range(0,len(text)-4,4):
 w=word(off)
 if (w>>26)!=0b100101: continue
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 if off+(imm<<2)==0x77B560: hits2.append(off)
print('dispatcher_direct_callsites',[hex(x) for x in hits2]); chk('unique_dispatcher_direct_caller',hits2==[0x257534])
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 ss=p.read_text()
 if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p117a.yml']
p116=(root/'.github/workflows/build-subsdk9-p116a.yml').read_text()
chk('p116_workflow_disabled','workflow_dispatch:' in p116 and not re.search(r'^\s{2}push:\s*$',p116,re.M))
print('P117A_DROPIN_SOURCE_VERIFY=PASS')
