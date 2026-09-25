#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P115B — boot-safe cinematic event-type preflight provenance')
assert start>=0
block=cpp[start:]

def chk(n,v):
    print(n,'PASS' if v else 'FAIL')
    assert v,n

checks={
 'entrypoint':'nsc::InstallP115BEventGateProbe();' in main,
 'decl':'void InstallP115BEventGateProbe();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P115B] READY' in block,
 'evt_log':'[NSC:P115B] EVT_GATE' in block,
 'event_offset':'kP115BEventTypeLoadOffset = 0x77C474' in block,
 'actor_fingerprint_offset':'kP115BActorC48CallOffset = 0x77C490' in block,
 'peer_fingerprint_offset':'kP115BPeerC48CallOffset = 0x77C4A4' in block,
 'type9_proof':'kP115BType9QueryCallOffset = 0x77C4B0' in block,
 'outer_proof':'kP115BOuterSetupCallOffset = 0x77C5E8' in block,
 'one_p115b_inline_hook':cpp.count('HOOK_DEFINE_INLINE(P115B')==1,
 'zero_p115b_trampolines':'HOOK_DEFINE_TRAMPOLINE(P115B' not in cpp,
 'one_p115b_install':block.count('P115BEventTypeLoadHook::InstallAtOffset')==1,
 'no_actor_c48_install':'P115BActorC48CallHook::InstallAtOffset' not in block,
 'no_peer_c48_install':'P115BPeerC48CallHook::InstallAtOffset' not in block,
 'p115a_runtime_absent':'[NSC:P115A]' not in cpp and 'InstallP115APreflightGateTripletProbe' not in cpp,
 'p114_runtime_absent':'[NSC:P114A]' not in cpp and 'P114APreflightType9QueryHook' not in cpp,
 'p113_runtime_absent':'[NSC:P113A]' not in cpp and 'P113ACinematicSessionSetupHook' not in cpp,
 'p112_runtime_absent':'[NSC:P112B]' not in cpp and '[NSC:P112A]' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'native_ldr_replayed':'ctx->W[8] = raw_type;' in block,
 'no_virtual_call_intercept':'P115C48Fn' not in block and 'P115BCallNativeC48' not in block,
 'one_extra_budget_claim':'one_extra_trampoline_budget=1' in block,
 'no_session_create_claim':'no_session_create=1' in block,
 'no_branch_patch_claim':'no_branch_patch=1' in block,
}
for k,v in checks.items(): chk(k,v)
code_only=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
chk('no_actor_memory_write',not re.search(r'\*reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',code_only))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',code_only))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_only))
# conservative logger buffer guard (LoggerMgr buffer = 512)
out=[]
for m in re.finditer(r'Logging\.Log\((.*?)\);',block,re.S):
    expr=m.group(1); lits=re.findall(r'"((?:\\.|[^"\\])*)"',expr)
    if not lits: continue
    fmt=''.join(bytes(x,'utf8').decode('unicode_escape') for x in lits)
    if '[NSC:P115B]' not in fmt: continue
    total=0; last=0
    for fm in re.finditer(r'%(?:0?8)?(?:l)?[duxp]',fmt):
        total+=len(fmt[last:fm.start()]); sp=fm.group(0)
        if sp in ('%u','%d'): total+=11
        elif sp=='%08x': total+=8
        elif sp=='%lx': total+=16
        elif sp=='%p': total+=18
        last=fm.end()
    total+=len(fmt[last:]); out.append((fmt.split()[1],total))
print('p115b_log_bounds',out); chk('p115b_log_buffer_guard',bool(out) and all(n<512 for _,n in out))

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
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,0x77C480:0x54000B81,
 0x77C484:0xF9400268,0x77C488:0xAA1303E0,0x77C48C:0xF9462508,0x77C490:0xD63F0100,0x77C494:0x34000AC0,
 0x77C498:0xF94002E8,0x77C49C:0xAA1703E0,0x77C4A0:0xF9462508,0x77C4A4:0xD63F0100,0x77C4A8:0x34000A20,
 0x77C4AC:0x52800120,0x77C4B0:0x97FF50EC,0x77C4B4:0x34000300,
 0x77C5E4:0xAA1703E0,0x77C5E8:0x9401CAAC,0x77C5EC:0xB9405288,
}
for off,w in expected.items():
    g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w

def bl_target(off):
    w=word(off); assert (w>>26)==0b100101
    imm=w&0x03ffffff
    if imm&0x02000000: imm-=0x04000000
    return off+(imm<<2)
for off,target in [(0x77C4B0,0x750860),(0x77C5E8,0x7EF098)]:
    g=bl_target(off); print('call',hex(off),'->',hex(g)); assert g==target
for lit in ('0xB9405288, 0x121F7909, 0x7100293F, 0x54000B81',
            '0xF9400268, 0xAA1303E0, 0xF9462508, 0xD63F0100, 0x34000AC0',
            '0xF94002E8, 0xAA1703E0, 0xF9462508, 0xD63F0100, 0x34000A20',
            '0x52800120, 0x97FF50EC, 0x34000300',
            '0xAA1703E0, 0x9401CAAC, 0xB9405288'):
    chk('runtime_sig_'+lit.split(',')[0].lower(),lit in block)
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    ss=p.read_text()
    if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p115b.yml']
print('P115B_DROPIN_SOURCE_VERIFY=PASS')
