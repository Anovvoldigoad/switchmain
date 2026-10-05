#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
root=Path(__file__).resolve().parent
cpp=root/'overlay/source/program/nsc_cpk_bridge.cpp'
core=root/'overlay/source/program/nsc_runtime_core.cpp'
hpp=root/'overlay/source/program/nsc_cpk_bridge.hpp'
wf=root/'.github/workflows/build-runtime-r181.yml'
req=[cpp,core,hpp,wf]
for p in req:
    if not p.is_file(): raise SystemExit(f'R264_SOURCE_VERIFY=FAIL missing={p}')
s=cpp.read_text()
need=[
'kR264WaitEnterOffset          = 0x549950',
'kR264SecondaryBuildOffset     = 0x6EB554',
'kR264DrawOffset               = 0x54ADA0',
'kR264DrawSubmitOffset         = 0x5B3AC',
'R264SecondaryBuildHook','R264FileResourceLookupHook','R264ChunkResourceLookupHook',
'R264DrawHook','R264DrawSubmitHook','SECONDARY_BUILD_PRE','SECONDARY_BUILD_POST',
'SECONDARY_FILE_LOOKUP','SECONDARY_CHUNK_LOOKUP','DRAW_PRE','DRAW_SUBMIT',
'cpk_bind=0 main_patch=0 gameplay_patch=0 id_patch=0 path_rewrite=0 return_override=0',
]
for x in need:
    if x not in s: raise SystemExit(f'R264_SOURCE_VERIFY=FAIL missing_marker={x}')
if 'return nsc::InstallR264SecondaryPreviewDrawTrace();' not in core.read_text():
    raise SystemExit('R264_SOURCE_VERIFY=FAIL installer_not_selected')
if 'bool InstallR264SecondaryPreviewDrawTrace();' not in hpp.read_text():
    raise SystemExit('R264_SOURCE_VERIFY=FAIL declaration_missing')
ws=wf.read_text()
for x in ['verify_r264.py','NSC2Switch-R264-SECONDARY-PREVIEW-DRAW-TRACE']:
    if x not in ws: raise SystemExit(f'R264_SOURCE_VERIFY=FAIL workflow_marker={x}')
# Source-only safety gates: no R264 path/return/ID/state override markers.
for bad in ['R264_PATH_REWRITE','R264_RETURN_OVERRIDE','R264_ID_PATCH','R264_FORCE_STATE']:
    if bad in s: raise SystemExit(f'R264_SOURCE_VERIFY=FAIL unsafe_marker={bad}')
print('R264_TARGET_SCOPE=mtobcharsel')
print('R264_SECONDARY_BUILDER=0x6EB554')
print('R264_DRAW_GATE=0x54ADA0')
print('R264_DRAW_SUBMIT=0x5B3AC')
print('R264_READONLY=PASS')
print('R264_SOURCE_VERIFY=PASS')
