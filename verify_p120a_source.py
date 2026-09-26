from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P120A — FIRST CORRECTIVE PATCH')
assert start>=0
block=cpp[start:]

def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n

checks={
 'entrypoint':'nsc::InstallP120ACustomUjCinematicGateBridge();' in main,
 'decl':'void InstallP120ACustomUjCinematicGateBridge();' in hpp,
 'ready':'[NSC:P120A] READY' in block,
 'gate_log':'[NSC:P120A] GATE' in block,
 'gate_offset':'kP120GateLoadOffset = 0x77C474' in block,
 'native_ldr_replayed':'native_raw' in block and 'event + 0x50u' in block and 'ctx->W[8] = out_raw;' in block,
 'semantic707':'atk.semantic != 0u && atk.action == 707u' in block,
 'generic_custom':'atk.cid > kVanillaMaxCharId && atk.cid < 0x1000u' in block,
 'opposite_side':'atk.side != victim_side' in block,
 'fresh_gap':'trace_gap <= kP120TraceGapMax' in block,
 'gap_is_16':'kP120TraceGapMax = 16u' in block,
 'appended_threshold':'kP120VanillaDamageCount = 1847u' in block,
 'appended_guard':'idx >= static_cast<int32_t>(kP120VanillaDamageCount)' in block,
 'native_gate_preserved':'((native_raw & ~1u) == 10u)' in block,
 'one_shot_latch':'g_p120_bridged_actor' in block and 'one_shot = true' in block,
 'latch_reset':'P120ObserveAttackerAction(actor, side, st.action);' in cpp,
 'snapshot_both_sides':'if (!actor || side > 1u) return;' in cpp,
 'one_p120_inline':cpp.count('HOOK_DEFINE_INLINE(P120')==1,
 'zero_p120_trampoline':'HOOK_DEFINE_TRAMPOLINE(P120' not in cpp,
 'one_p120_install':cpp.count('P120CustomUjCinematicGateHook::InstallAtOffset')==1,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'no_p119_install':'InstallP118BEventTableIdentityInternal();' not in block,
 'no_fixture_damage_string_literals':'"DMG_MTOB_SPL' not in block and '"DAMAGE_ID_SPATK_BEGIN_DIRECT' not in block,
 'no_char281_branch':not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)', block),
 'no_force708':'force708' not in block.lower() or 'no_force708' in block,
 'no_force710':'force710' not in block.lower() or 'no_force710' in block,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
}
for k,v in checks.items(): chk(k,v)

# Remove comments/strings and reject direct game-memory writes in P120 block.
code_no_comments=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',block,flags=re.M|re.S)
# The only intended write is ctx->W[8] and plugin-local atomics. No dereferenced pointer assignment.
chk('no_direct_game_pointer_write', not re.search(r'\*reinterpret_cast<[^>]+>\([^\n;]*\)\s*=', code_no_comments))
chk('no_b9e4_write', '0xB9E4' not in code_no_comments and '0xb9e4' not in code_no_comments)
chk('no_session_create_call', '0x7EF098' not in block and '0x7ef098' not in block)
chk('no_action_setter_call', 'kCentralActionSetterOffset' not in block and '0x766320' not in block)

# Conservative log bounds.
def bound_for(tag,max_s=0):
    calls=[x for x in re.findall(r'Logging\.Log\((.*?)\);',block,re.S) if tag in x]
    assert calls,tag
    x=calls[-1]
    lits=re.findall(r'"((?:\\.|[^"\\])*)"',x)
    f=''.join(bytes(z,'utf8').decode('unicode_escape') for z in lits)
    total=0; last=0
    for m in re.finditer(r'%(?:0?8)?(?:l)?[duxps]',f):
        total += len(f[last:m.start()]); sp=m.group(0)
        if sp in ('%u','%d'): total+=11
        elif sp=='%08x': total+=8
        elif sp=='%lx': total+=16
        elif sp=='%p': total+=18
        elif sp=='%s': total+=max_s
        last=m.end()
    total+=len(f[last:])
    print('log_bound',tag,total)
    chk(tag.replace('[NSC:P120A] ','').lower()+'_lt_512',total<512)
bound_for('[NSC:P120A] GATE')
bound_for('[NSC:P120A] READY')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

# Paired-main exact v1.70 gate fingerprint.
b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]
tf,tm,ts=struct.unpack_from('<III',b,0x10); assert (flags&1)==0
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected={
 0x77C474:0xB9405288,0x77C478:0x121F7909,0x77C47C:0x7100293F,0x77C480:0x54000B81,
 0x77C484:0xF9400268,0x77C488:0xAA1303E0,0x77C48C:0xF9462508,0x77C490:0xD63F0100,
 0x77C494:0x34000AC0,0x77C498:0xF94002E8,0x77C49C:0xAA1703E0,0x77C4A0:0xF9462508,
 0x77C4A4:0xD63F0100,0x77C4A8:0x34000A20,0x77C4AC:0x52800120,0x77C4B0:0x97FF50EC,
 0x77C5E4:0xAA1703E0,0x77C5E8:0x9401CAAC,0x77C5EC:0xB9405288,
}
for off,w in expected.items():
    got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w

# Ensure only P120 workflow auto-runs on push.
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    ss=p.read_text()
    if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p120a.yml']
print('P120A_DROPIN_SOURCE_VERIFY=PASS')
