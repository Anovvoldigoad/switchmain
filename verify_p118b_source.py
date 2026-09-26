from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P118B — exact event cursor / table identity census')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P118BEventTableIdentityHook)',start)
he=cpp.find('static bool InstallP118BEventTableIdentityInternal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('hook_abi_u32_event_x0','static uint32_t Callback(void* event_x0)' in h)
chk('capture_lr_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'MainRelativeOffset(caller_lr)'))
chk('capture_x19_before_helpers',pos(h,'asm volatile("mov %0, x19"') < pos(h,'MainRelativeOffset(caller_lr)'))
chk('fast_passthrough_before_table_reads',pos(h,'if (caller_off != kP118BFocusedCallerReturn)') < pos(h,'const uintptr_t main_base'))
chk('orig_two_textual_paths',len(re.findall(r'\bOrig\s*\(',h))==2)
chk('fast_orig_unchanged','return Orig(event_x0);' in h)
chk('focused_orig_once_at_end',h.rstrip().endswith('};') and 'return Orig(event_x0);' in h)
checks={
 'entrypoint':'nsc::InstallP118BEventTableIdentityProbe();' in main,
 'decl':'void InstallP118BEventTableIdentityProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P118B] READY' in block,
 'cursor_log':'[NSC:P118B] CURSOR' in block,
 'record_log':'[NSC:P118B] REC' in block,
 'table_log':'[NSC:P118B] TABLE' in block,
 'getter_offset':'kP118BEventGateGetterOffset = 0x3F4BC0' in block,
 'lookup_offset':'kP118BEventLookupOffset = 0x3F4B00' in block,
 'name_offset':'kP118BEventNameOffset = 0x3F4B60' in block,
 'focused_return':'kP118BFocusedCallerReturn = 0x77B5AC' in block,
 'root_global':'kP118BEventRootGlobalOffset = 0x2143488' in block,
 'record_stride':'kP118BRecordStride = 0x60u' in block,
 'radius_32':'kP118BRadius = 32' in block,
 'direct_cursor_read':'ab + 0xB9E4u' in block,
 'count_read':'container + 0x50u' in block,
 'records_base_read':'container + 0x48u' in block,
 'names_base_read':'container + 0x58u' in block,
 'global_a8_read':'container + 0xA8u' in block,
 'x19_actor':'caller_x19' in block,
 'cursor_ptr_match':'cursor_ptr_match' in block,
 'event_ptr_match':'expected_ptr_match' in block,
 'one_p118_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P118')==1,
 'no_p118_inline':'HOOK_DEFINE_INLINE(P118' not in cpp,
 'p118a_runtime_absent':'[NSC:P118A]' not in cpp and 'InstallP118AEventNeighborhoodCensusProbe' not in main,
 'p117_runtime_absent':'[NSC:P117A]' not in cpp and 'P117' not in main,
 'p116_runtime_absent':'[NSC:P116A]' not in cpp,
 'p115_runtime_absent':'[NSC:P115' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_pointer_write',not re.search(r'\*reinterpret_cast<[^>]+>\([^\n;]*\)\s*=',code_only))
chk('cursor_read_only','*reinterpret_cast<const volatile uint16_t*>(ab + 0xB9E4u)' in block)
chk('no_branch_patch','WriteInst' not in block and 'HOOK_DEFINE_INLINE' not in block)
chk('no_session_create','0x7514AC' not in block and '0x750C78' not in block)
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# Conservative LoggerMgr 512-byte estimates for P118B lines.
for tag,fmt,max_s in [
 ('CURSOR', next(x for x in re.findall(r'Logging\.Log\((.*?)\);',block,re.S) if '[NSC:P118B] CURSOR' in x), 63),
 ('TABLE', next(x for x in re.findall(r'Logging\.Log\((.*?)\);',block,re.S) if '[NSC:P118B] TABLE' in x), 0),
 ('REC', next(x for x in re.findall(r'Logging\.Log\((.*?)\);',block,re.S) if '[NSC:P118B] REC' in x), 47),
]:
 lits=re.findall(r'"((?:\\.|[^"\\])*)"',fmt)
 f=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
 total=0; last=0
 for m in re.finditer(r'%(?:0?8)?(?:l)?[duxps]',f):
  total+=len(f[last:m.start()]); sp=m.group(0)
  if sp in ('%u','%d'): total+=11
  elif sp=='%08x': total+=8
  elif sp=='%lx': total+=16
  elif sp=='%p': total+=18
  elif sp=='%s': total+=max_s
  last=m.end()
 total+=len(f[last:])
 print('p118b_log_bound',tag,total); chk(f'{tag.lower()}_log_lt_512',total<512)

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
# Key static proof: direct actor/cursor, record table, name table, existing getter boundary.
for off,w in {
 0x3F4B00:0x13003C08,0x3F4B08:0xF000EA68,0x3F4B0C:0xF9424508,
 0x3F4B10:0xF9760908,0x3F4B14:0xF9405D08,0x3F4B18:0xB9405109,
 0x3F4B24:0xF9402508,0x3F4B2C:0x52800C0A,0x3F4B30:0x9B0A2120,
 0x3F4B60:0x13003C08,0x3F4B68:0xF000EA68,0x3F4B6C:0xF9424508,
 0x3F4B70:0xF9760908,0x3F4B74:0xF9405D08,0x3F4B78:0xB9405109,
 0x3F4B84:0xF9402D08,0x3F4B8C:0x5280060A,0x3F4B90:0x9B0A212A,
 0x3F4BC0:0xF000EA68,0x3F4BCC:0xF9405D08,0x3F4BD0:0x79415100,
 0x77B584:0x52973C88,0x77B588:0xAA0003F3,0x77B58C:0x78686800,
 0x77B590:0x97F1E55C,0x77B5A0:0x79449375,0x77B5A4:0xAA0003F4,
 0x77B5A8:0x97F1E586,0x77B5AC:0x6B2022BF,
}.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
print('bl 77b590 ->',hex(bl_target(0x77B590))); assert bl_target(0x77B590)==0x3F4B00
print('bl 77b5a8 ->',hex(bl_target(0x77B5A8))); assert bl_target(0x77B5A8)==0x3F4BC0
# The ADRP+LDR pair in both lookup tables resolves main+0x2143488.
chk('event_root_static_offset',0x2143000+0x488==0x2143488)
# index->name helper has exactly one direct native caller in v1.70; P118B calls it diagnostically.
hits=[]
for off in range(0,len(text)-4,4):
 w=word(off)
 if (w>>26)!=0b100101: continue
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 if off+(imm<<2)==0x3F4B60: hits.append(off)
print('name_getter_direct_callsites',[hex(x) for x in hits]); chk('name_getter_native_single_caller',hits==[0x77BFE8])
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 ss=p.read_text()
 if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p118b.yml']
p118a=(root/'.github/workflows/build-subsdk9-p118a.yml').read_text()
chk('p118a_workflow_disabled','workflow_dispatch:' in p118a and not re.search(r'^\s{2}push:\s*$',p118a,re.M))
print('P118B_DROPIN_SOURCE_VERIFY=PASS')
