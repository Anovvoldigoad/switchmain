#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,struct,sys
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main_cpp=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
workflow=(root/'.github/workflows/build-subsdk9-p62a.yml').read_text()
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

ck('calls_p62','InstallP62APersistentUjControlGetter();' in main_cpp)
ck('no_main_p61_call','InstallP61AUjEligibilityGateCompat();' not in main_cpp)
ck('hpp_p62_decl','void InstallP62APersistentUjControlGetter();' in hpp)
ck('p62_ready_marker','[NSC:P62A] READY' in cpp)
ck('p62_getter_marker','[NSC:P62A] CTRL_GET_UJ_PERSIST' in cpp)
ck('p62_hook_defined','HOOK_DEFINE_TRAMPOLINE(NativeControlGetterCompatHook)' in cpp)
ck('p62_getter_install','NativeControlGetterCompatHook::InstallAtOffset(kNativeControlGetterOffset);' in cpp)
ck('p62_capture_x30_before_orig',re.search(r'NativeControlGetterCompatHook.*?asm volatile\("mov %0, x30".*?const int32_t raw = Orig\(',cpp,re.S) is not None)
ck('p62_orig_first_semantics',re.search(r'const int32_t raw = Orig\(control_object, selector\);.*?if \(raw != 0 \|\| selector != kNativeUltimateJutsuSelector',cpp,re.S) is not None)
ck('p62_exact_selector8','selector != kNativeUltimateJutsuSelector' in cpp and 'kNativeUltimateJutsuSelector     = 8' in cpp)
ck('p62_control_object_to_actor','reinterpret_cast<uint8_t*>(control_object) - kNativeControlObjectOffset' in cpp)
ck('p62_generic_custom_guard','char_id > kVanillaMaxCharId && char_id < 0x1000u' in cpp)
ck('p62_source_enable_registry','IsP62UjEnabled(actor)' in cpp and 'MarkP62UjEnabled(actor);' in cpp)
ck('p62_source_disable_registry','if (p2 == 0 && p3 == 1) ClearP62UjEnabled(actor);' in cpp)
ck('p62_raw_nonzero_preserved','raw != 0' in cpp and 'return raw;' in cpp)
ck('p62_only_virtual_return','returned=1' in cpp)
ck('p62_ready_flag','g_p62_native_getter_ready' in cpp)
ck('p62_no_p61_gate_hook','UjEligibilityGateHook' not in cpp and '[NSC:P61A] UJ_GATE_COMPAT' not in cpp)
ck('p62_no_f58_install','0x7D3138' not in cpp and 'kUjEligibilityGateOffset' not in cpp)
ck('p62_verify_before_event236',re.search(r'void InstallP62APersistentUjControlGetter\(\).*?VerifyP60NativeUjControlPort\(\);.*?InstallP62PersistentUjControlGetter\(\);.*?InstallP50AConditionCompat\(\);',cpp,re.S) is not None)
ck('total_hooks_8','total_trampolines=8' in cpp)
ck('victim_shadows_retained','victim_shadows_retained=1' in cpp and '[NSC:P50A] VIS_SHADOW' in cpp and '[NSC:P50A] OP15_SHADOW' in cpp and '[NSC:P50A] OP17_SHADOW' in cpp and '[NSC:P50A] OP18_SHADOW' in cpp)
ck('no_char281_gameplay_if',not re.search(r'if\s*\([^\n]*char_id\s*==\s*281',cpp))
# Restrict force/write checks to P62 getter hook body.
m=re.search(r'HOOK_DEFINE_TRAMPOLINE\(NativeControlGetterCompatHook\)(.*?)// P59A:',cpp,re.S)
hook_body=m.group(1) if m else ''
ck('p62_no_action700_force','700' not in hook_body and 'PlayAction' not in hook_body)
ck('p62_no_state87_force','0x87' not in hook_body and '135' not in hook_body and '0xE94' not in hook_body and '0xE9C' not in hook_body)
ck('p62_no_actor_control_write','EnableNativeUltimateJutsuControl' not in hook_body and '+ 0x670' not in hook_body and '+0x670' not in hook_body)
ck('deploy_main_p50',sha(deploy)=='8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be')
ck('restore_main',sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')

# Binary fingerprints: exact native API and both downstream UJ-router selector8 reads.
ck('native_getter_entry',words(0x7C6280,6)==[0xF81E0FFE,0xA9014FF4,0x2A0103F3,0xAA0003F4,0x71004C3F,0x54000161])
ck('native_getter_indexed_load',words(0x7C62C0,2)==[0x8B33CA88,0xB9442900])
ck('native_enable',words(0x7C65B0,4)==[0x8B21C808,0x52800029,0xB9042909,0xD65F03C0])
ck('uj_router_slot8_first',words(0xC7928,4)==[0xAA1403E0,0x52800101,0x941BFA54,0x35000120] and bl_target(0xC7930,word(0xC7930))==0x7C6280)
ck('uj_router_state87',word(0xC795C)==0x528010F5)
ck('uj_router_slot8_second',words(0xC79A4,4)==[0xAA1403E0,0x52800101,0x941BFA35,0x340000C0] and bl_target(0xC79AC,word(0xC79AC))==0x7C6280)
ck('uj_router_state_request_df0',words(0xC79BC,3)==[0x2A1503E1,0xF946F908,0xD63F0100])
ck('wrong_call_445_owner',word(0x7B4B2C)==0x97FEC818 and bl_target(0x7B4B2C,word(0x7B4B2C))==0x766B8C)

ck('ci_elf_extract','ELF_EXTRACT := $(PWD)/p62a_final.elf' in prepare)
ck('ci_checks_p62_elf',"grep -aFq '[NSC:P62A] READY' \"$ELF\"" in workflow and "grep -aFq '[NSC:P62A] CTRL_GET_UJ_PERSIST' \"$ELF\"" in workflow)
ck('ci_rejects_p61_gate_marker',"if grep -aFq '[NSC:P61A] UJ_GATE_COMPAT' \"$ELF\"" in workflow)
ck('ci_nso_magic','nso[:4] != b"NSO0"' in workflow)
ck('no_prebuilt_subsdk9',not any(p.name=='subsdk9' for p in root.rglob('subsdk9')))

failed=[n for n,v in checks if not v]
for n,v in checks: print(f'{n}={"PASS" if v else "FAIL"}')
if failed:
    print('P62A_VERIFY=FAIL '+','.join(failed)); sys.exit(1)
print('P62A_VERIFY=PASS')
print('active_trampolines=8')
print('functional_delta=persistent_source_UJ_enable_at_native_selector8_getter')
print('native_getter=0x7c6280')
print('native_selector=8')
print('f58_override=0')
print('no_action_force=1')
print('no_state_force=1')
print('deploy_main_sha256='+sha(deploy))
print('restore_main_sha256='+sha(restore))
