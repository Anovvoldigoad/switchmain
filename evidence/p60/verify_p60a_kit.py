#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,struct,sys

root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main_cpp=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
workflow=(root/'.github/workflows/build-subsdk9-p60a.yml').read_text()
prepare=(root/'prepare_exlaunch.sh').read_text()
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

ck('calls_p60','InstallP60ANativeUjControlPort();' in main_cpp)
ck('hpp_decl','void InstallP60ANativeUjControlPort();' in hpp)
ck('p60_ready_marker','[NSC:P60A] READY' in cpp)
ck('p60_port_marker','[NSC:P60A] CTRL14_UJ_PORT' in cpp)
ck('p60_fail_marker','[NSC:P60A] CTRL14_UJ_PORT_FAIL' in cpp)
ck('p59_mode_retained','[NSC:P59A] MODE_BASE' in cpp and 'InstallP59ActionModeBaseTrace();' in cpp)
ck('p59_play_retained','[NSC:P59A] PLAY_CALL' in cpp)
ck('native_get_const','kNativeControlGetterOffset       = 0x7C6280' in cpp)
ck('native_enable_const','kNativeControlEnableOffset       = 0x7C65B0' in cpp)
ck('native_control_object','kNativeControlObjectOffset       = 0x228' in cpp)
ck('native_uj_slot8','kNativeUltimateJutsuSelector     = 8' in cpp)
ck('native_api_fingerprinted','VerifyP60NativeUjControlPort()' in cpp and 'P60_CONTROL_GET' in cpp and 'P60_CONTROL_ENABLE' in cpp)
ck('verify_before_event236',re.search(r'void InstallP60ANativeUjControlPort\(\).*?VerifyP60NativeUjControlPort\(\);\s*InstallP50AConditionCompat\(\);',cpp,re.S) is not None)
ck('only_self_uj_source_map','if (p2 == 0 && p3 == 1 &&' in cpp)
ck('calls_native_enable','enable(control_object, kNativeUltimateJutsuSelector);' in cpp)
ck('reads_before_after','const int32_t before = ReadNativeControl' in cpp and 'const int32_t after = ReadNativeControl' in cpp)
ck('other_op14_shadow','[NSC:P60A] CTRL14_SHADOW' in cpp)
ck('op15_still_shadow','[NSC:P50A] OP15_SHADOW' in cpp)
ck('op17_still_shadow','[NSC:P50A] OP17_SHADOW' in cpp)
ck('op18_still_shadow','[NSC:P50A] OP18_SHADOW' in cpp)
ck('no_char281_gameplay_if',not re.search(r'if\s*\([^\n]*char_id\s*==\s*281',cpp))
ck('no_445_700_rewrite',not re.search(r'index\s*==\s*445[^\n]{0,160}(700|=\s*700)',cpp))
ck('no_state87_write',not re.search(r'\+\s*0xE94\)[^;\n]*=\s*(0x87|135)',cpp))
ck('no_direct_slot670_write','+ 0x670' not in cpp and '+0x670' not in cpp)
ck('ready_7','total_trampolines=7' in cpp)
ck('ci_elf_extract','ELF_EXTRACT := $(PWD)/p60a_final.elf' in prepare)
ck('ci_checks_linked_elf',"grep -aFq '[NSC:P60A] READY' \"$ELF\"" in workflow and "grep -aFq '[NSC:P60A] CTRL14_UJ_PORT' \"$ELF\"" in workflow and "grep -aFq '[NSC:P59A] MODE_BASE' \"$ELF\"" in workflow and "grep -aFq '[NSC:P59A] PLAY_CALL' \"$ELF\"" in workflow)
ck('ci_nso_magic_check','nso[:4] != b"NSO0"' in workflow)
ck('deploy_main_p50',sha(deploy)=='8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be')
ck('restore_main',sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')

# Exact native control API fingerprints.
ck('getter_7c6280',words(0x7C6280,6)==[0xF81E0FFE,0xA9014FF4,0x2A0103F3,0xAA0003F4,0x71004C3F,0x54000161])
ck('getter_indexed_load',words(0x7C62C0,2)==[0x8B33CA88,0xB9442900])
ck('enable_7c65b0',words(0x7C65B0,4)==[0x8B21C808,0x52800029,0xB9042909,0xD65F03C0])

# UJ router proof: native selector8 -> state0x87 -> virtual state request +0xDF0.
ck('uj_router_slot8',words(0xC7928,4)==[0xAA1403E0,0x52800101,0x941BFA54,0x35000120] and bl_target(0xC7930,word(0xC7930))==0x7C6280)
ck('uj_router_state87',word(0xC795C)==0x528010F5)
ck('uj_state_request_df0',words(0xC79BC,3)==[0x2A1503E1,0xF946F908,0xD63F0100])

# Native code also enables selector8 around UJ-state logic.
ck('native_slot8_setter_site_a',words(0x3B4218,3)==[0x9108A100,0x52800101,0x941048E4] and bl_target(0x3B4220,word(0x3B4220))==0x7C65B0)
ck('native_slot8_state87_site_b',word(0x3B432C)==0x71021D3F and words(0x3B4350,3)==[0x9108A100,0x52800101,0x94104896] and bl_target(0x3B4358,word(0x3B4358))==0x7C65B0)

# P59 wrong-route diagnostics retained and exact.
ck('mode_base_7b468c',words(0x7B468C,4)==[0xD10243FF,0xFD001BE8,0xF9001FFE,0xA9046FFC])
w=word(0x7B4B2C)
ck('wrong_call_is_bl_playaction',w==0x97FEC818 and bl_target(0x7B4B2C,w)==0x766B8C)

ck('no_prebuilt_subsdk9',not any(p.name=='subsdk9' for p in root.rglob('subsdk9')))

failed=[n for n,v in checks if not v]
for n,v in checks: print(f'{n}={"PASS" if v else "FAIL"}')
if failed:
    print('P60A_VERIFY=FAIL '+','.join(failed)); sys.exit(1)
print('P60A_VERIFY=PASS')
print('active_trampolines=7')
print('functional_delta=Event236_op14_p2_0_p3_1_to_native_slot8')
print('native_getter=0x7c6280')
print('native_enable=0x7c65b0')
print('native_uj_selector=8')
print('no_action_force=1')
print('no_state_force=1')
print('deploy_main_sha256='+sha(deploy))
print('restore_main_sha256='+sha(restore))
