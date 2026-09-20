#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,struct,sys

root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main_cpp=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
deploy=root/'deploy/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def nso_text(path):
    b=path.read_bytes()
    if b[:4] != b'NSO0': raise AssertionError('deploy main is not NSO0')
    flags=struct.unpack_from('<I',b,0x0c)[0]
    file_off,mem_off,size=struct.unpack_from('<III',b,0x10)
    comp_size=struct.unpack_from('<I',b,0x60)[0]
    if mem_off != 0: raise AssertionError('unexpected text memory offset')
    if flags & 1: raise AssertionError('text compression unexpected in pinned P50 main')
    if comp_size != size: raise AssertionError('text size mismatch')
    return b[file_off:file_off+size]

text=nso_text(deploy)
def word(off): return struct.unpack_from('<I',text,off)[0]
def words(off,n): return [word(off+4*i) for i in range(n)]

def bl_target(off,w):
    if (w & 0xfc000000) != 0x94000000: return None
    imm=w & 0x03ffffff
    if imm & (1<<25): imm -= 1<<26
    return off + (imm<<2)

checks=[]
def ck(name,cond): checks.append((name,bool(cond)))

ck('calls_p59','InstallP59AActionModeDispatchTrace();' in main_cpp)
ck('hpp_decl','void InstallP59AActionModeDispatchTrace();' in hpp)
ck('mode_hook_defined','HOOK_DEFINE_TRAMPOLINE(ActionModeBaseHook)' in cpp)
ck('mode_hook_installed','ActionModeBaseHook::InstallAtOffset(kActionModeBaseOffset);' in cpp)
ck('p59_capture_x30',re.search(r'ActionModeBaseHook\).*?asm volatile\("mov %0, x30"',cpp,re.S) is not None)
ck('p59_mode_marker','[NSC:P59A] MODE_BASE' in cpp)
ck('p59_play_marker','[NSC:P59A] PLAY_CALL' in cpp)
ck('play_all_side0','const bool p59_log = valid && (side == 0u || custom);' in cpp)
ck('slot_e40_read','vtable + kActionModeVtableSlotOffset' in cpp and 'kActionModeVtableSlotOffset    = 0xE40' in cpp)
ck('ready_7','total_trampolines=7 writes=0' in cpp)
ck('central_setter_retained','InstallP57CentralSetterTrace();' in cpp)
ck('no_char281_gameplay_if',not re.search(r'if\s*\([^\n]*char_id\s*==\s*281',cpp))
ck('no_445_700_rewrite',not re.search(r'index\s*==\s*445[^\n]{0,120}(700|=\s*700)',cpp))
ck('no_event236_unshadow','CTRL14_SHADOW' in cpp)
ck('deploy_main_p50',sha(deploy)=='8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be')
ck('restore_main',sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')

# Exact pinned-binary architectural fingerprints.
ck('thunk_7b4680', words(0x7B4680,3)==[0xF9400008,0xF9472102,0xD61F0040])
ck('base_7b468c', words(0x7B468C,10)==[
    0xD10243FF,0xFD001BE8,0xF9001FFE,0xA9046FFC,0xA90567FA,
    0xA9065FF8,0xA90757F6,0xA9084FF4,0x7100203F,0x54008648])
ck('mode0_literal445', word(0x7B4758)==0x528037A1)
ck('mode0_resolver_slot1488', word(0x7B4760)==0xF94A4508)
ck('mode0_e94_read', word(0x7B476C)==0xB94E9668)
ck('common_tail_mov_w1_w21', word(0x7B4B20)==0x2A1503E1)
w=word(0x7B4B2C)
ck('wrong_call_is_bl_playaction', w==0x97FEC818 and bl_target(0x7B4B2C,w)==0x766B8C)
ck('base_epilogue_ret', word(0x7B5798)==0xD65F03C0)

# Build kit must not accidentally ship the old compiled P58 subsdk9.
ck('no_prebuilt_subsdk9',not any(p.name=='subsdk9' for p in root.rglob('subsdk9')))

failed=[n for n,v in checks if not v]
for n,v in checks: print(f'{n}={"PASS" if v else "FAIL"}')
if failed:
    print('P59A_VERIFY=FAIL '+','.join(failed)); sys.exit(1)
print('P59A_VERIFY=PASS')
print('active_trampolines=7')
print('added_over_p58=1')
print('gameplay_writes_added=0')
print('dispatch_thunk=0x7b4680')
print('dispatch_vslot=0xe40')
print('base_impl=0x7b468c')
print('wrong_play_callsite=0x7b4b2c->0x766b8c')
print('deploy_main_sha256='+sha(deploy))
print('restore_main_sha256='+sha(restore))
