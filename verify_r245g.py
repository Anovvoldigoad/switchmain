#!/usr/bin/env python3
from pathlib import Path
import hashlib, struct, sys
try:
    import lz4.block
except Exception:
    lz4 = None

ROOT = Path(__file__).resolve().parent
CPP = (ROOT/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
HPP = (ROOT/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
CORE = (ROOT/'overlay/source/program/nsc_runtime_core.cpp').read_text()
WF = (ROOT/'.github/workflows/build-runtime-r181.yml').read_text()
MAIN = ROOT/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
EXPECTED_MAIN_SHA = '2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

checks = {
    'core_calls_r245g_only': 'return nsc::InstallR245GPreviewStateGateTrace();' in CORE,
    'no_gameplay_installer_in_core': all(x not in CORE for x in [
        'InstallP128','InstallR172','InstallR175','InstallR176','InstallR177',
        'InstallV2N','InstallV2P','InstallResolverHookMigrationProbe','InstallOriginalMainRuntimePatches']),
    'public_decl': 'bool InstallR245GPreviewStateGateTrace();' in HPP,
    'ready_marker': '[NSC:R245G] READY' in CPP and 'readonly=1' in CPP,
    'gate_enter_marker': '[NSC:R245G] GATE_ENTER' in CPP,
    'gate_exit_marker': '[NSC:R245G] GATE_EXIT' in CPP,
    'gate_registry_marker': '[NSC:R245G] GATE_REGISTRY_PROCESS' in CPP,
    'alt_ready_marker': '[NSC:R245G] GATE_ALT_READY' in CPP,
    'gate_offset': 'kR245GPreviewStateGateOffset = 0x549804' in CPP,
    'alt_offset': 'kR245GAltReadyWrapperOffset  = 0x58498' in CPP,
    'gate_installed': 'R245GPreviewStateGateHook::InstallAtOffset(kR245GPreviewStateGateOffset);' in CPP,
    'alt_installed': 'R245GAltReadyWrapperHook::InstallAtOffset(kR245GAltReadyWrapperOffset);' in CPP,
    'orig_once_gate': CPP[CPP.index('HOOK_DEFINE_TRAMPOLINE(R245GPreviewStateGateHook)'):CPP.index('HOOK_DEFINE_TRAMPOLINE(R245GAltReadyWrapperHook)')].count('Orig(self);') == 2,
    # Two textual sites are intentional: one early passthrough before target exists, one traced branch. Exactly one executes per call.
    'orig_once_alt': CPP[CPP.index('HOOK_DEFINE_TRAMPOLINE(R245GAltReadyWrapperHook)'):CPP.index('HOOK_DEFINE_TRAMPOLINE(LoadOwnerStateHook)')].count('Orig(p)') == 1,
    'no_cpk_bind_current_installer': 'CpkBindHook::Install' not in CPP[CPP.index('bool InstallR245GPreviewStateGateTrace()'):CPP.index('bool InstallPlayActionProbe()')],
    'no_mutation_flags': all(x in CPP for x in ['cpk_bind=0','main_patch=0','gameplay_patch=0','id_patch=0','path_rewrite=0','return_override=0']),
    'workflow_verifies_r245g': 'python3 verify_r245g.py' in WF,
    'workflow_artifact_r245g': 'NSC2Switch-R245G-PREVIEW-STATE-GATE-TRACE' in WF,
    'workflow_no_main_assert': 'test ! -e out/runtime/atmosphere/contents/0100FA10190A0000/exefs/main' in WF,
}
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()): sys.exit(1)

raw = MAIN.read_bytes()
print('original_main_sha256=' + hashlib.sha256(raw).hexdigest())
if hashlib.sha256(raw).hexdigest() != EXPECTED_MAIN_SHA:
    print('original_main_sha256_match=FAIL'); sys.exit(1)
print('original_main_sha256_match=PASS')

def decode_text(raw: bytes) -> bytes:
    if raw[:4] != b'NSO0': raise RuntimeError('not NSO0')
    u = lambda o: struct.unpack_from('<I', raw, o)[0]
    flags, fo, sz, csz = u(0x0c), u(0x10), u(0x18), u(0x60)
    blob = raw[fo:fo+(csz if flags & 1 else sz)]
    if flags & 1:
        if lz4 is None: raise RuntimeError('lz4 required for compressed NSO')
        blob = lz4.block.decompress(blob, uncompressed_size=sz)
    return blob

text = decode_text(raw)
def words(off, n): return list(struct.unpack_from('<'+'I'*n, text, off))
checks2 = {
    'gate_fingerprint': words(0x549804, 8) == [
        0xA9BF4FFE,0xAA0003F3,0xF9405400,0xB4000260,
        0x94306121,0x34000220,0xF9406260,0xB40000C0],
    'gate_second_half': words(0x549824, 14) == [
        0x97EC3B1B,0x35000080,0xF9406260,0x97EC3B1A,0x34000140,
        0xF9404268,0xF85E8100,0xB40000E0,0x94306115,0x340000A0,
        0x52800028,0xB9006E68,0x52800048,0xB9005E68],
    'mid_registry_wrapper_fingerprint': words(0x58490,2) == [0x91002000,0x14442601],
    'alt_state_wrapper_fingerprint': words(0x58498,2) == [0x91002000,0x14442621],
    'registry_process_fingerprint': words(0x1161C98,8) == [
        0xF81E0FFE,0xA9014FF4,0xF9400C14,0x91008013,
        0x14000002,0xAA0903F4,0xEB13029F,0x540002E0],
    'registry_state_fingerprint': words(0x1161D20,8) == [
        0xF81E0FFE,0xA9014FF4,0xF9400C14,0x91008013,
        0x14000002,0xAA0903F4,0xEB13029F,0x540002E0],
}
for k,v in checks2.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if not all(checks2.values()): sys.exit(1)
print('R245G_SOURCE_VERIFY=PASS')
