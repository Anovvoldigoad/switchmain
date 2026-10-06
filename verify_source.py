from pathlib import Path
import hashlib

root = Path(__file__).resolve().parent
cpp = (root / "overlay/source/program/nsc_cpk_bridge.cpp").read_text()
main = (root / "overlay/source/program/main.cpp").read_text()
prep = (root / "prepare_exlaunch.sh").read_text()

required_cpp = [
    'kCpkBindOffset = 0x473190',
    'kModCpkPriority = 32',
    'sim:data/moddingapi/Tobi_Switch.cpk',
    'CpkBindHook::InstallAtOffset(kCpkBindOffset)',
    '0xF81D0FFE, 0xA90157F6, 0xA9024FF4, 0xD000E6A8',
    '0xF945ED08, 0xAA0003F5, 0xF9400100, 0xB4000200',
    'Orig(desc, out_bind_id, priority)',
    'Orig(&extra, &extra_bind_id, kModCpkPriority)',
]
for s in required_cpp:
    assert s in cpp, f'missing required source token: {s}'

# This source package must remain mount-only. No historical diagnostic/gameplay hooks.
forbidden = [
    'CharacodeGetterHook', 'FileLoadRequestHook', 'FileLoadCreateHook',
    'FileLoadStatusHook', 'ChunkBinaryHook', 'LoadRequestProcessHook',
    'FileOpenHook', 'Event236Hook', 'Event235Hook', 'Event13Hook',
    'Event121Hook', 'OugiCoreHook', 'OugiCallerHook', 'StageHandleHook',
    'FixCharPositionHook', 'PostStageHook', 'PlayAction', 'ACTION_LOOKUP',
    'VIS_SHADOW', 'CTRL14_SHADOW',
]
for s in forbidden:
    assert s not in cpp, f'forbidden non-mount hook/token present: {s}'

assert 'exl::hook::Initialize()' in main
assert 'nsc::InstallMinimalCpkBridge()' in main
assert 'LOAD_KIND := Module' in prep
assert 'PROGRAM_ID := 0100FA10190A0000' in prep
assert 'CXX_FLAGS := -Wno-non-c-typedef-for-linkage' in prep

print('===== SOURCE HASHES =====')
for rel in [
    'overlay/source/program/main.cpp',
    'overlay/source/program/nsc_cpk_bridge.cpp',
    'overlay/source/program/nsc_cpk_bridge.hpp',
    'prepare_exlaunch.sh',
]:
    b = (root / rel).read_bytes()
    print(hashlib.sha256(b).hexdigest(), rel)

print('R276H19B_SOURCE_SCOPE=PASS')
print('R276H19B_ACTIVE_HOOK_COUNT=1')
print('R276H19B_ACTIVE_HOOK=main+0x473190_CPK_BIND')
