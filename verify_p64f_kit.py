#!/usr/bin/env python3
from pathlib import Path
import struct, hashlib
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main_cpp=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
workflow=(root/'.github/workflows/build-subsdk9-p64f.yml').read_text()
prepare=(root/'prepare_exlaunch.sh').read_text()
mainp=root/'deploy/atmosphere/contents/0100FA10190A0000/exefs/main'
mainbin=mainp.read_bytes()
assert mainbin[:4]==b'NSO0'
text_off=struct.unpack_from('<I',mainbin,0x10)[0]
text_size=struct.unpack_from('<I',mainbin,0x18)[0]
text=mainbin[text_off:text_off+text_size]

def words(off,n):
    return list(struct.unpack_from('<'+'I'*n,text,off))

def ck(name,v):
    print(f'{name}={"PASS" if v else "FAIL"}')
    if not v: raise SystemExit(1)

ck('main_calls_p64f','InstallP64FUjSemanticBridge();' in main_cpp)
ck('hpp_decl','void InstallP64FUjSemanticBridge();' in hpp)
ck('workflow_p64f','Build NSC P64F UJ Semantic Bridge' in workflow)
ck('prepare_elf','p64f_final.elf' in prepare)
ck('semantic_set_marker','[NSC:P64F] UJ_SEM_SET' in cpp)
ck('semantic_gate_marker','[NSC:P64F] UJ_SEM_GATE' in cpp)
ck('semantic_consumer_hook','HOOK_DEFINE_TRAMPOLINE(P64SemanticUjConsumerHook)' in cpp)
ck('consumer_install','P64SemanticUjConsumerHook::InstallAtOffset(kUjSemanticConsumerOffset);' in cpp)
ck('selector1_enable','if (p3 == 1)' in cpp and 'P64SetSemanticUltimateJutsu(target, true);' in cpp)
ck('selector1_disable','P64SetSemanticUltimateJutsu(target, false);' in cpp)
ck('no_selector8_bridge','CTRL_GET_UJ_PERSIST' not in cpp and 'CTRL14_UJ_PORT' not in cpp)
ck('no_force700','index = 700' not in cpp and 'return 700' not in cpp)
ck('no_force87','*reinterpret_cast<volatile int32_t*>(reinterpret_cast<uint8_t*>(actor) + 0xE94) = 0x87' not in cpp)
ck('no_rejected_control_write','kRejectedControlBlockOffset' in cpp and 'P64SetSemanticUltimateJutsu' in cpp)

# main+0x7ABE9C helper entry
ck('consumer_entry',words(0x7ABE9C,8)==[
    0xF81E0FFE,0xA9014FF4,0xB94E9408,0x51002908,
    0xAA0003F3,0x7100091F,0x54000188,0x5280D288])
# selector1 native getter call in helper
ck('consumer_selector1_query',words(0x7ABF28,4)==[
    0x9108A260,0x52800021,0x940068D4,0x7100001F])
# exact UJ router callsites -> helper
ck('router_call0',words(0xC76C0,2)==[0x941B91F7,0x35000180])
ck('router_call1',words(0xC76EC,2)==[0x941B91EC,0x34000160])
ck('router_call2',words(0xC78D0,2)==[0x941B9173,0x35FFF100])
# downstream native state remains native
ck('state87_native',words(0xC7958,2)==[0x2A1F03F9,0x528010F5])
ck('paired_main_sha',hashlib.sha256(mainbin).hexdigest()=='8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be')
restore=(root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main').read_bytes()
ck('restore_main_sha',hashlib.sha256(restore).hexdigest()=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')
print('P64F_VERIFY=PASS')
