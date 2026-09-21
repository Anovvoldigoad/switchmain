#!/usr/bin/env python3
from pathlib import Path
import struct,re
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
mainbin=(root/'deploy/atmosphere/contents/0100FA10190A0000/exefs/main').read_bytes()
assert mainbin[:4]==b'NSO0'
text_off=struct.unpack_from('<I',mainbin,0x10)[0]
text_size=struct.unpack_from('<I',mainbin,0x18)[0]
text=mainbin[text_off:text_off+text_size]
def words(off,n): return list(struct.unpack_from('<'+'I'*n,text,off))
def ck(name,v):
 print(f'{name}={"PASS" if v else "FAIL"}')
 if not v: raise SystemExit(1)
ck('calls_p63','InstallP63AUjRouterFirstDivergenceTrace();' in main)
ck('hpp_decl','void InstallP63AUjRouterFirstDivergenceTrace();' in hpp)
ck('p60_removed','InstallP60' not in main and 'CTRL14_UJ_PORT' not in cpp)
ck('p61_removed','UjEligibilityGateHook' not in cpp and 'UJ_GATE_COMPAT' not in cpp)
ck('p62_removed','CTRL_GET_UJ_PERSIST' not in cpp)
ck('p63_f58_hook','HOOK_DEFINE_TRAMPOLINE(P63UjEligibilityTraceHook)' in cpp)
ck('p63_post_hook','HOOK_DEFINE_TRAMPOLINE(P63UjPostGateHelperTraceHook)' in cpp)
ck('p63_getter_hook','HOOK_DEFINE_TRAMPOLINE(P63NativeControlGetterTraceHook)' in cpp)
ck('f58_entry',words(0x7D3138,9)==[0xFC1C0FE8,0xA9015FFE,0xA90257F6,0xA9034FF4,0x5281E808,0x72A00028,0xB8686808,0x2A010108,0x340000C8])
ck('post_gate_entry',words(0x7D2DE4,8)==[0xF81E0FFE,0xA9014FF4,0xF9400008,0x2A0103F4,0xAA0003F3,0xF946E508,0xD63F0100,0x34000320])
ck('control_getter',words(0x7C6280,6)==[0xF81E0FFE,0xA9014FF4,0x2A0103F3,0xAA0003F4,0x71004C3F,0x54000161])
ck('router_f58',words(0xC7860,6)==[0xF9400268,0xAA1303E0,0x2A1F03E1,0xF947AD08,0xD63F0100,0x34000340])
ck('state87_native',words(0xC7958,2)==[0x2A1F03F9,0x528010F5])
ck('no_force700','index = 700' not in cpp and 'return 700' not in cpp)
ck('no_force87','0x87;' not in cpp and '0x87)' not in cpp)
print('P63A_VERIFY=PASS')
