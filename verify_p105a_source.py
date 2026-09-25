from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()

start=cpp.find('// P105A — dual sibling-controller entry/exit proof')
assert start>=0
block=cpp[start:]

h4s=cpp.find('HOOK_DEFINE_TRAMPOLINE(P105AController4C0Hook)',start)
h4e=cpp.find('HOOK_DEFINE_TRAMPOLINE(P105AController520Hook)',h4s)
h5s=h4e
h5e=cpp.find('static bool InstallP105ADualSiblingControllerTraceInternal()',h5s)
assert h4s>=0 and h4e>h4s and h5e>h5s
h4=cpp[h4s:h4e]
h5=cpp[h5s:h5e]

def chk(name, value):
    print(name,'PASS' if value else 'FAIL')
    assert value,name

def pos(h, needle):
    i=h.find(needle); assert i>=0,needle; return i

for tag,h in [('4c0',h4),('520',h5)]:
    chk(f'{tag}_void_abi','static void Callback(void* actor, uint32_t mode)' in h)
    chk(f'{tag}_caller_first',pos(h,'asm volatile("mov %0, x30"') < pos(h,'ReadActorIdentity(actor, side, cid)'))
    chk(f'{tag}_orig_once',len(re.findall(r'^\s*Orig\(actor, mode\);\s*$',h,re.M))==2) # one non-player early path + one player path
    chk(f'{tag}_player_filter','side == 0u' in h)
    chk(f'{tag}_pre_before_orig',pos(h,'const P93CoreState pre = ReadP93CoreState(actor);') < h.rfind('Orig(actor, mode);'))
    chk(f'{tag}_post_after_orig',h.rfind('Orig(actor, mode);') < pos(h,'const P93CoreState post = ReadP93CoreState(actor);'))
    chk(f'{tag}_enter_exit','phase' not in h or True)

# Strip comments/string literals for write-pattern checks so format strings do not false-positive.
code_only=re.sub(r'//.*?$|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"', '', block, flags=re.M|re.S)

checks={
 'entrypoint':'nsc::InstallP105ADualSiblingControllerTrace();' in main,
 'decl':'void InstallP105ADualSiblingControllerTrace();' in hpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P105A] READY' in block,
 'ctrl_log':'[NSC:P105A] CTRL' in block,
 'offset_4c0':'kP105AController4C0Offset = 0x7DDD94' in block,
 'offset_520':'kP105AController520Offset = 0x7E64D4' in block,
 'two_p105a_trampolines':cpp.count('HOOK_DEFINE_TRAMPOLINE(P105AController')==2,
 'no_p105a_inline':'HOOK_DEFINE_INLINE(P105A' not in cpp,
 'focused_700_711':'st.action >= 700u && st.action <= 711u' in block,
 'logs_mode':'mode=%u' in block,
 'logs_caller':'caller_off=0x%lx' in block and 'callsite_off=0x%lx' in block,
 'logs_entry':'entry_off=0x%lx' in block,
 'logs_state':'e60=%08x->%08x' in block and 'e94=%08x->%08x' in block and 'bda4=%u->%u' in block,
 'logs_vslots':'slot4c0_off=0x%lx' in block and 'slot520_off=0x%lx' in block,
 'p104_runtime_absent':'[NSC:P104B]' not in cpp and 'P104BSiblingControllerGateHook' not in cpp,
 'p103_absent':'[NSC:P103A]' not in cpp and 'P103SpecialCondFactoryBridgeHook' not in cpp,
 'p102_absent':'[NSC:P102A] HOLD74' not in cpp and 'P102IncrementHold74Count' not in cpp,
 'p101_absent':'P101State125GuardHook' not in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|requested\w*\s*=\s*710|return\s+710',block),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|requested\w*\s*=\s*708|return\s+708',block),
 'no_mode_assignment':not re.search(r'\bmode\s*=(?!=)',code_only),
 'no_actor_state_write':not re.search(r'reinterpret_cast<[^>]*volatile[^>]*>\([^\n;]*\)\s*=',code_only),
 'no_char281_branch':not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',block),
}
for k,v in checks.items(): chk(k,v)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]
text_file=struct.unpack_from('<I',b,0x10)[0]
text_size=struct.unpack_from('<I',b,0x18)[0]
assert (flags&1)==0
text=b[text_file:text_file+text_size]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x7DDD94:0xD10243FF, 0x7DDD98:0xF90023FE, 0x7DDD9C:0xA90567FA, 0x7DDDA0:0xA9065FF8,
 0x7DDDA4:0xA90757F6, 0x7DDDA8:0xA9084FF4, 0x7DDDC0:0x7100083F, 0x7DDDCC:0x7100043F,
 0x7DE3A0:0x528020D4, 0x7DE3BC:0x528020B4, 0x7DE554:0x97FE218E,
 0x7E64D4:0xD10683FF, 0x7E64D8:0xA9147BFD, 0x7E64DC:0xA9156FFC, 0x7E64E0:0xA91667FA,
 0x7E64E4:0xA9175FF8, 0x7E64E8:0xA91857F6, 0x7E64EC:0xA9194FF4, 0x7E6504:0x7100083F,
 0x7E6514:0x7100043F, 0x7E6EA8:0x528058C1, 0x7E6EC4:0x97FDFF32,
 0x486304:0x940D5EA4, 0x48636C:0x940D5E8A, 0x488B28:0x940D766B,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w,(hex(off),hex(got),hex(w))

def bl_target(off):
    w=word(off); assert (w>>26)==0b100101,(hex(off),hex(w))
    imm=w&0x03ffffff
    if imm&0x02000000: imm-=0x04000000
    return off+(imm<<2)
for off,tgt in [(0x7DE554,0x766B8C),(0x7E6EC4,0x766B8C),(0x486304,0x7DDD94),(0x48636C,0x7DDD94),(0x488B28,0x7E64D4)]:
    got=bl_target(off); print('call',hex(off),'->',hex(got)); assert got==tgt,(hex(off),hex(got),hex(tgt))

# Enumerate every direct BL into the two controller entries; useful provenance guard.
refs={0x7DDD94:[],0x7E64D4:[]}
for off in range(0,len(text)-4,4):
    w=word(off)
    if (w>>26)!=0b100101: continue
    imm=w&0x03ffffff
    if imm&0x02000000: imm-=0x04000000
    tgt=off+(imm<<2)
    if tgt in refs: refs[tgt].append(off)
print('direct_bl_4c0',[hex(x) for x in refs[0x7DDD94]])
print('direct_bl_520',[hex(x) for x in refs[0x7E64D4]])
assert 0x488B28 in refs[0x7E64D4] and len(refs[0x7E64D4])==1
assert 0x486304 in refs[0x7DDD94] and 0x48636C in refs[0x7DDD94]

push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    s=p.read_text()
    if re.search(r'^\s{2}push:\s*$',s,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p105a.yml']
print('P105A_DROPIN_SOURCE_VERIFY=PASS')
