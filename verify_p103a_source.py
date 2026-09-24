from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
maph=(root/'overlay/source/program/p103_specialcond_map.hpp').read_text()
prep=(root/'prepare_exlaunch.sh').read_text()

start=cpp.find('// P103A — source-faithful SpecialCond factory selector bridge.')
assert start >= 0
block=cpp[start:]
hook_start=cpp.find('HOOK_DEFINE_TRAMPOLINE(P103SpecialCondFactoryBridgeHook)', start)
hook_end=cpp.find('static bool InstallP103SpecialCondFactoryBridgeInternal()', hook_start)
hook=cpp[hook_start:hook_end]
play_start=cpp.find('HOOK_DEFINE_TRAMPOLINE(PlayActionProbeHook)')
play_end=cpp.find('// P64F-A:',play_start)
play=cpp[play_start:play_end]

checks={
 'entrypoint':'nsc::InstallP103ASpecialCondFactoryBridge();' in main,
 'decl':'void InstallP103ASpecialCondFactoryBridge();' in hpp,
 'map_include':'#include "p103_specialcond_map.hpp"' in cpp,
 'prepare_copies_map':'p103_specialcond_map.hpp' in prep,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in block,
 'ready':'[NSC:P103A] READY' in block,
 'remap_log':'[NSC:P103A] REMAP' in hook,
 'dispatcher_offset':'kP103SpecialCondDispatcherOffset = 0x7CAB00' in block,
 'one_p103_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P103SpecialCondFactoryBridgeHook)') == 1,
 'no_p103_inline':'HOOK_DEFINE_INLINE(P103' not in cpp,
 'map_call':'p103_data::MapSpecialCondSelector(selector)' in hook,
 'orig_once':hook.count('Orig(') == 1,
 'context_preserved':'Orig(mapped, context)' in hook,
 'map_281_58':'{281u, 58u}' in maph,
 'map_276_276':'{276u, 276u}' in maph,
 'map_count_2':'kSpecialCondMapCount' in maph and maph.count('{281u, 58u}')==1,
 'p102_hold_absent':'[NSC:P102A] HOLD74' not in cpp and 'P102IncrementHold74Count' not in cpp and 'P102ResetHold74Count' not in cpp,
 'p101_state_guard_absent':'HOOK_DEFINE_TRAMPOLINE(P101State125GuardHook)' not in cpp,
 'victim_shadow_preserved':'case 12:' in cpp and 'VIS_SHADOW' in cpp and 'case 14:' in cpp and 'CTRL14_SHADOW' in cpp,
 'no_force710':not re.search(r'Orig\s*\([^\n]*710|selector\s*=\s*710|return\s+710',block+hook+play),
 'no_force708':not re.search(r'Orig\s*\([^\n]*708|selector\s*=\s*708|return\s+708',block+hook+play),
 'no_actor_field_write':not re.search(r'reinterpret_cast<volatile[^>]*>\([^\)]*\+\s*0xE54[^\)]*\)\s*=',hook,re.I),
 'no_action_write':not re.search(r'\+\s*(?:4712|0x1268)\)\s*=',hook),
 'no_state_write':not re.search(r'\+\s*0x(?:E94|E9C|EA4|BDA4|BDA8|BDC8)\)\s*=',hook,re.I),
 'no_char281_gameplay_branch':not re.search(r'(?:selector|char_id|cid)\s*==\s*281|281\s*==\s*(?:selector|char_id|cid)',cpp),
}
for k,v in checks.items():
 print(k,'PASS' if v else 'FAIL'); assert v,k

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

# Pinned paired main has uncompressed text. Prove dispatcher + direct callsite.
b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]
text_file=struct.unpack_from('<I',b,0x10)[0]
text_size=struct.unpack_from('<I',b,0x18)[0]
assert (flags & 1)==0, 'paired text unexpectedly compressed'
text=b[text_file:text_file+text_size]
def word(off): return struct.unpack_from('<I',text,off)[0]
expected_sig={
 0x7CAB00:0xF81E0FFE,
 0x7CAB04:0xA9014FF4,
 0x7CAB08:0x51015008,
 0x7CAB0C:0x2A0003F3,
 0x7CAB10:0x7100B91F,
 0x7CAB14:0x54000548,
 0x7CAB18:0xB0009C29,
 0x7CAB1C:0x912F8129,
 0x722F24:0xB9400340, # LDR W0,[X26]
 0x722F28:0xB942FF81, # LDR W1,[X28,#0x2FC]
}
for off,w in expected_sig.items():
 got=word(off); print(f'fp {off:#x}',f'{got:08x}','PASS' if got==w else 'FAIL'); assert got==w
bl=word(0x722F2C); assert (bl & 0xFC000000)==0x94000000
imm=bl & 0x03FFFFFF
if imm & 0x02000000: imm-=0x04000000
target=0x722F2C + imm*4
print('call 0x722F2C ->',hex(target)); assert target==0x7CAB00

# Active workflow safety: legacy workflows may remain in a long-lived repo,
# but exactly P103A may be push-enabled. Manual workflow_dispatch-only
# historical files are harmless and are intentionally allowed.
push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
 s=p.read_text()
 if re.search(r'^\s{2}push:\s*$',s,re.M):
  push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p103a.yml']
print('P103A_DROPIN_SOURCE_VERIFY=PASS')
