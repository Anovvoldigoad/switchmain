#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P114A — exact type9 preflight provenance')
assert start>=0
block=cpp[start:]
hs=cpp.find('HOOK_DEFINE_TRAMPOLINE(P114APreflightType9QueryHook)',start)
he=cpp.find('static bool InstallP114APreflightType9Internal()',hs)
assert hs>=0 and he>hs
h=cpp[hs:he]
def chk(n,v): print(n,'PASS' if v else 'FAIL'); assert v,n
def pos(s,n):
 i=s.find(n); assert i>=0,n; return i
chk('query_abi_u32','static uint32_t Callback(uint32_t type)' in h)
chk('caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'MainRelativeOffset(caller_lr)'))
chk('focus_before_logging',pos(h,'if (caller_off != kP114FocusedCallerReturn || type != 9u)') < pos(h,'g_p114_count.fetch_add'))
chk('orig_two_textual_paths',len(re.findall(r'\bOrig\s*\(',h))==2)
chk('fast_passthrough','return Orig(type);' in h)
chk('focused_orig_unchanged','const uint32_t ret = Orig(type);' in h)
checks={
 'entrypoint':'nsc::InstallP114APreflightType9Probe();' in main,
 'decl':'void InstallP114APreflightType9Probe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P114A] READY' in block,
 'preflight_log':'[NSC:P114A] PREFLIGHT' in block,
 'query_offset':'kP114SessionQueryOffset = 0x750860' in block,
 'caller_return':'kP114FocusedCallerReturn = 0x77C4B4' in block,
 'event_gate':'kP114EventTypeGateOffset = 0x77C474' in block,
 'type9_filter':'type != 9u' in h,
 'one_p114_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P114')==1,
 'no_p114_inline':'HOOK_DEFINE_INLINE(P114' not in cpp,
 'p113_runtime_absent':'[NSC:P113A]' not in cpp and 'P113ACinematicSessionSetupHook' not in cpp,
 'p112_runtime_absent':'[NSC:P112B]' not in cpp and '[NSC:P112A]' not in cpp,
 'p111_runtime_absent':'[NSC:P111A]' not in cpp,
 'p110_runtime_absent':'[NSC:P110A]' not in cpp,
 'p109_runtime_absent':'[NSC:P109A]' not in cpp,
 'p108_runtime_absent':'[NSC:P108A]' not in cpp,
 'p107_runtime_absent':'[NSC:P107A]' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_manual_session_claim':'no_session_create=1' in block,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_direct_state_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# LoggerMgr has a fixed 512-byte buffer: conservatively bound P114 lines.
out=[]
for m in re.finditer(r'Logging\.Log\((.*?)\);',block,re.S):
 expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
 if not lits: continue
 fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
 if '[NSC:P114A]' not in fmt: continue
 total=0; last=0
 for fm in re.finditer(r'%(?:0?8)?(?:l)?[duxp]',fmt):
  total+=len(fmt[last:fm.start()]); sp=fm.group(0)
  if sp in ('%u','%d'): total+=11
  elif sp=='%08x': total+=8
  elif sp=='%lx': total+=16
  elif sp=='%p': total+=18
  last=fm.end()
 total+=len(fmt[last:]); out.append((fmt.split()[1],total))
print('p114_log_bounds',out); chk('p114_log_buffer_guard',bool(out) and all(n<512 for _,n in out))
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
 0x750860:0xB000CFE8,0x750864:0xF9404108,0x750868:0xF9400109,0x75086C:0xB40001C9,
 0x750888:0xB9403D2A,0x750894:0xB940392A,0x75089C:0x52800020,
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,0x77C480:0x54000B81,
 0x77C484:0xF9400268,0x77C488:0xAA1303E0,0x77C48C:0xF9462508,0x77C490:0xD63F0100,0x77C494:0x34000AC0,
 0x77C498:0xF94002E8,0x77C49C:0xAA1703E0,0x77C4A0:0xF9462508,0x77C4A4:0xD63F0100,0x77C4A8:0x34000A20,
 0x77C4AC:0x52800120,0x77C4B0:0x97FF50EC,0x77C4B4:0x34000300,
 0x77C514:0xAA1303E0,0x77C518:0x9400666E,0x77C51C:0x9401ECF8,0x77C520:0xB40003E0,
 0x77C5E4:0xAA1703E0,0x77C5E8:0x9401CAAC,0x77C5EC:0xB9405288,
 0x7EF098:0xF81E0FFE,
}
for off,w in expected.items():
 g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w

def bl_target(off):
 w=word(off); assert (w>>26)==0b100101
 imm=w&0x03ffffff
 if imm&0x02000000: imm-=0x04000000
 return off+(imm<<2)
for off,target in [(0x77C4B0,0x750860),(0x77C518,0x795ED0),(0x77C51C,0x7F78FC),(0x77C5E8,0x7EF098)]:
 g=bl_target(off); print('call',hex(off),'->',hex(g)); assert g==target
# Verify source runtime signatures use the same paired-main words (prevents P112A-style mismatch).
for lit in ('0xB9405288, 0x121F7909, 0x7100293F, 0x54000B81',
            '0x52800120, 0x97FF50EC, 0x34000300',
            '0xAA1303E0, 0x9400666E, 0x9401ECF8, 0xB40003E0',
            '0xAA1703E0, 0x9401CAAC, 0xB9405288'):
 chk('runtime_sig_'+lit.split(',')[0].lower(),lit in block)
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 ss=p.read_text()
 if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p114a.yml']
print('P114A_DROPIN_SOURCE_VERIFY=PASS')
