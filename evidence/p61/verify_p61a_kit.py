#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,struct,sys
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main_cpp=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
workflow=(root/'.github/workflows/build-subsdk9-p61a.yml').read_text()
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

ck('calls_p61','InstallP61AUjEligibilityGateCompat();' in main_cpp)
ck('hpp_decl','void InstallP61AUjEligibilityGateCompat();' in hpp)
ck('p61_ready_marker','[NSC:P61A] READY' in cpp)
ck('p61_gate_marker','[NSC:P61A] UJ_GATE_COMPAT' in cpp)
ck('p61_gate_const','kUjEligibilityGateOffset          = 0x7D3138' in cpp)
ck('p61_router_callsite','kUjRouterGateCallsiteOffset       = 0xC7870' in cpp)
ck('p61_router_return','kUjRouterGateReturnOffset         = 0xC7874' in cpp)
ck('p61_local_flag','kUjEligibilityLocalFlagOffset     = 0x10F40' in cpp)
ck('p61_mark_on_source_enable',re.search(r'if \(p2 == 0 && p3 == 1 &&.*?MarkP61UjEnabled\(actor\);.*?EnableNativeUltimateJutsuControl',cpp,re.S) is not None)
ck('p61_private_clear_only','if (p2 == 0 && p3 == 1) ClearP61UjEnabled(actor);' in cpp)
ck('p61_hook_defined','HOOK_DEFINE_TRAMPOLINE(UjEligibilityGateHook)' in cpp)
ck('p61_capture_x30',re.search(r'UjEligibilityGateHook.*?asm volatile\("mov %0, x30"',cpp,re.S) is not None)
ck('p61_preserve_native_true','if (orig != 0) return orig;' in cpp)
ck('p61_generic_custom_guard','char_id > kVanillaMaxCharId && char_id < 0x1000u' in cpp)
ck('p61_exact_lr_guard','caller_off == kUjRouterGateReturnOffset' in cpp)
ck('p61_mode0_guard','exact_router && mode == 0u && source_enabled' in cpp)
ck('p61_source_enable_guard','IsP61UjEnabled(actor)' in cpp)
ck('p61_refresh_slot8','EnableNativeUltimateJutsuControl(actor, side, char_id)' in cpp)
ck('p61_returns_gate_only',re.search(r'UjEligibilityGateHook.*?return 1;',cpp,re.S) is not None)
ck('p61_install','UjEligibilityGateHook::InstallAtOffset(kUjEligibilityGateOffset);' in cpp)
ck('verify_before_event236',re.search(r'void InstallP61AUjEligibilityGateCompat\(\).*?VerifyP60NativeUjControlPort\(\);.*?InstallP61UjEligibilityGateCompat\(\);.*?InstallP50AConditionCompat\(\);',cpp,re.S) is not None)
ck('total_hooks_8','total_trampolines=8' in cpp)
ck('victim_shadows_retained','victim_shadows_retained=1' in cpp and '[NSC:P50A] VIS_SHADOW' in cpp and '[NSC:P50A] OP15_SHADOW' in cpp and '[NSC:P50A] OP17_SHADOW' in cpp and '[NSC:P50A] OP18_SHADOW' in cpp)
ck('no_char281_gameplay_if',not re.search(r'if\s*\([^\n]*char_id\s*==\s*281',cpp))
# Restrict force checks to the new P61 hook body, avoiding historical diagnostic strings elsewhere.
m=re.search(r'HOOK_DEFINE_TRAMPOLINE\(UjEligibilityGateHook\)(.*?)// P59A:',cpp,re.S)
hook_body=m.group(1) if m else ''
ck('p61_no_action700_force','700' not in hook_body and 'PlayAction' not in hook_body)
ck('p61_no_state87_force','0x87' not in hook_body and '135' not in hook_body and '0xE94' not in hook_body and '0xE9C' not in hook_body)
ck('p61_no_direct_slot_write','+ 0x670' not in hook_body and '+0x670' not in hook_body)
ck('deploy_main_p50',sha(deploy)=='8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be')
ck('restore_main',sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')

# P60 native control support still fingerprints exactly.
ck('native_getter',words(0x7C6280,6)==[0xF81E0FFE,0xA9014FF4,0x2A0103F3,0xAA0003F4,0x71004C3F,0x54000161])
ck('native_enable',words(0x7C65B0,4)==[0x8B21C808,0x52800029,0xB9042909,0xD65F03C0])
# Exact F58 implementation entry and its first local actor eligibility field read.
ck('f58_gate_entry',words(0x7D3138,9)==[0xFC1C0FE8,0xA9015FFE,0xA90257F6,0xA9034FF4,0x5281E808,0x72A00028,0xB8686808,0x2A010108,0x340000C8])
# Exact native router virtual dispatch. LR after BLR is 0xC7874.
ck('router_f58_call',words(0xC7860,6)==[0xF9400268,0xAA1303E0,0x2A1F03E1,0xF947AD08,0xD63F0100,0x34000340])
ck('router_callsite_blr',word(0xC7870)==0xD63F0100)
ck('router_return_cbz',word(0xC7874)==0x34000340)
# Prove selector8 is downstream, not the root gate: it appears after F58 return check.
ck('slot8_after_f58',words(0xC7928,4)==[0xAA1403E0,0x52800101,0x941BFA54,0x35000120] and bl_target(0xC7930,word(0xC7930))==0x7C6280)
ck('state87_downstream',word(0xC795C)==0x528010F5)
ck('state_request_df0',words(0xC79BC,3)==[0x2A1503E1,0xF946F908,0xD63F0100])
# Data availability check inside F58 family retained; P61 does not forge it directly.
ck('f58_index6_check',words(0x7D3270,4)==[0xAA1303E0,0x528000C1,0x97FF0944,0x34FFF7C0] and bl_target(0x7D3278,word(0x7D3278))==0x795788)
# Existing wrong-route instrumentation remains exact.
ck('wrong_call_445_owner',word(0x7B4B2C)==0x97FEC818 and bl_target(0x7B4B2C,word(0x7B4B2C))==0x766B8C)

ck('ci_elf_extract','ELF_EXTRACT := $(PWD)/p61a_final.elf' in prepare)
ck('ci_checks_p61_elf',"grep -aFq '[NSC:P61A] READY' \"$ELF\"" in workflow and "grep -aFq '[NSC:P61A] UJ_GATE_COMPAT' \"$ELF\"" in workflow)
ck('ci_nso_magic','nso[:4] != b"NSO0"' in workflow)
ck('no_prebuilt_subsdk9',not any(p.name=='subsdk9' for p in root.rglob('subsdk9')))

failed=[n for n,v in checks if not v]
for n,v in checks: print(f'{n}={"PASS" if v else "FAIL"}')
if failed:
    print('P61A_VERIFY=FAIL '+','.join(failed)); sys.exit(1)
print('P61A_VERIFY=PASS')
print('active_trampolines=8')
print('functional_delta=guarded_F58_false_to_true_at_exact_UJ_router_only')
print('gate=0x7d3138')
print('router_callsite=0xc7870')
print('router_return_lr=0xc7874')
print('native_slot8_refresh=1')
print('no_action_force=1')
print('no_state_force=1')
print('deploy_main_sha256='+sha(deploy))
print('restore_main_sha256='+sha(restore))
