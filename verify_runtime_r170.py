#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,struct,sys
try:
    import lz4.block
except Exception:
    lz4=None

root=Path(__file__).resolve().parent
rt=(root/'overlay/source/program/nsc_runtime_v2.cpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
prep=(root/'prepare_exlaunch.sh').read_text()
wf=(root/'.github/workflows/build-runtime-r170.yml').read_text()

checks={
 'main_order': main.index('InstallResolverHookMigrationProbe();') < main.index('InstallOriginalMainRuntimePatches()') < main.index('InstallP128AStaticPreciseGateCaveProof();') < main.index('InstallR170Uj707NativeGateProbe();') < main.index('InstallV2NStageRegistryProof();'),
 'fail_closed_main': 'if (!nsc::v2::InstallOriginalMainRuntimePatches()) return;' in main,
 'r169_not_installed': 'InstallR169CustomUj707WhiffRelease();' not in main,
 'r169_runtime_mutation_removed': '[NSC:R169] UJ707_WHIFF' not in bridge and 'direct(actor, 77, -1, 0, 1.0f);' not in bridge and 'direct(actor, 74, -1, 0, 1.0f);' not in bridge,
 'r170_installed': 'InstallR170Uj707NativeGateProbe();' in main and '[NSC:R170] READY installed=1 native_707_gate=0x769a4c' in bridge,
 'r170_exact_caller': 'kR170Uj707GateCallerReturnOffset = 0x7E48E8' in bridge and 'caller_off == kR170Uj707GateCallerReturnOffset' in bridge,
 'r170_readonly_orig': 'const uint32_t ret = Orig(actor);' in bridge and 'readonly=1' in bridge,
 'r170_reason_fields': all(x in bridge for x in ('busy1264','flags70','frame74','end78','duration_bits','tick_num','tick_div','timing_pass','reason=%s')),
 'r170_no_force': 'force708=0 force710=0' in bridge and 'direct77_74=0' in bridge,
 'stage_trace_hooks_omitted': 'InstallV2MStageSafeTraceHooks();' not in main,
 'voice_probes_not_installed': 'InstallR165Event150VoiceReadOnlyProbe();' not in main and 'InstallR166SoundDispatchReadOnlyProbe();' not in main,
 'p128_retained': '[NSC:P128A] READY' in bridge and 'no_force708=1' in bridge and 'no_force710=1' in bridge,
 'thirty_word_plan': 'WordPatch plan[30]' in rt and 'condition_words=5 p67_words=1 p128_words=24' in rt,
 'validate_before_write': rt.index('Validate ALL original words before the first write') < rt.index('patcher.Write<std::uint32_t>'),
 'workflow_r170': len(list((root/'.github/workflows').glob('*.yml')))==1 and 'NSC-RUNTIME-R170-uj707-native-gate-probe' in wf,
 'prepare_r170_elf': 'runtime_r170.elf' in prep,
}
for k,v in checks.items(): print(k,'PASS' if v else 'FAIL')
if not all(checks.values()): sys.exit(1)

def decode_text(path):
    b=path.read_bytes()
    if b[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',b,o)[0]
    flags=u(0x0c);fo=u(0x10);va=u(0x14);size=u(0x18);csz=u(0x60)
    blob=b[fo:fo+(csz if flags&1 else size)]
    if flags&1:
        if lz4 is None: raise RuntimeError('lz4 required')
        blob=lz4.block.decompress(blob,uncompressed_size=size)
    return va,blob

orig=root/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
ref=root/'reference_p128/atmosphere/contents/0100FA10190A0000/exefs/main'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if sha(orig)!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9':
    print('original_main_sha256 FAIL');sys.exit(1)
print('original_main_sha256 PASS')
va_o,o=decode_text(orig); va_r,r=decode_text(ref)
if va_o!=0 or va_r!=0 or len(o)!=len(r): sys.exit(1)
diff={off:(struct.unpack_from('<I',o,off)[0],struct.unpack_from('<I',r,off)[0])
      for off in range(0,len(o)-3,4)
      if struct.unpack_from('<I',o,off)[0]!=struct.unpack_from('<I',r,off)[0]}
print('reference_delta_30_words','PASS' if len(diff)==30 else 'FAIL',len(diff))
if len(diff)!=30: sys.exit(1)

def words(off,n): return [struct.unpack_from('<I',o,off+4*i)[0] for i in range(n)]
gate_exp=[0xFC1D0FE8,0xA90157FE,0xA9024FF4,0xAA0003F3,0xF9410C00,0xB4000160,0x97F34520,0xD000CEC8]
handler_exp=[0x97FE0875,0x710B141F,0x54001020,0x710B101F,0x54001160,0x710B0C1F,0x54002521,0xAA1303E0,0x97FE145A,0x340029E0,0x52805881,0xAA1303E0,0x52800022,0x97FE1163,0xB4002740,0xF9400268,0x1E2E1000,0x52805881,0xF947CD08,0x12800002,0xAA1303E0,0x2A1F03E3,0x913A9274,0xD63F0100,0xF900029F]
blocker_exp=[0xF9402808,0xB4000068,0x9100E000,0x14351C9E,0x2A1F03E0,0xD65F03C0]
flag_exp=[0x79407008,0x12000100,0xD65F03C0]
timing_exp=[0xB9407400,0xD65F03C0,0xB9407800,0xD65F03C0]
for name,got,exp in [
 ('r170_gate_fingerprint',words(0x769A4C,8),gate_exp),
 ('r170_707_handler_fingerprint',words(0x7E48C4,25),handler_exp),
 ('r170_inner_blocker_fingerprint',words(0x438E48,6),blocker_exp),
 ('r170_flag70_fingerprint',words(0x11800CC,3),flag_exp),
 ('r170_timer_fields_fingerprint',words(0x43BC70,4),timing_exp),
]:
    ok=got==exp; print(name,'PASS' if ok else 'FAIL')
    if not ok: sys.exit(1)

# Registry lookup remains exact; R164 CPK behavior is external/frozen.
reg_exp=[0xF8408C09,0xB40001A9,0xAA0003E8,0xB940212A,0x6B01015F,0x1A9F27EA,0x9A893108,0xF86A5929]
ok=words(0x8364F8,8)==reg_exp
print('stage_registry_fingerprint','PASS' if ok else 'FAIL')
if not ok: sys.exit(1)
print('NSC_RUNTIME_R170_SOURCE_VERIFY=PASS')
