#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parent
cpp=root/'overlay/source/program/nsc_cpk_bridge.cpp'
core=root/'overlay/source/program/nsc_runtime_core.cpp'
hpp=root/'overlay/source/program/nsc_cpk_bridge.hpp'
wf=root/'.github/workflows/build-runtime-r181.yml'
for p in [cpp,core,hpp,wf]:
    if not p.is_file(): raise SystemExit(f'R265_SOURCE_VERIFY=FAIL missing={p}')
s=cpp.read_text()
need=[
'kR264WaitEnterOffset          = 0x549950',
'kR264SecondaryBuildOffset     = 0x6EB554',
'kR264DrawOffset               = 0x54ADA0',
'kR264DrawSubmitOffset         = 0x5B3AC',
'kR265RenderObjectGateOffset   = 0x43F1F8',
'R264SecondaryBuildHook','R264FileResourceLookupHook','R264ChunkResourceLookupHook',
'R264DrawHook','R265DrawSubmitHook','R265RenderObjectGateHook',
'SECONDARY_BUILD_PRE','SECONDARY_BUILD_POST','SECONDARY_FILE_LOOKUP','SECONDARY_CHUNK_LOOKUP',
'SUBMIT_BEGIN','SUBMIT_END','RENDER_GATE','value4c_bits','final_fn','pass=%u',
'objects0=SUBMIT_LOOKUP_EMPTY','objects_gt0_pass0=RENDER_OBJECT_GATE_BLOCK',
'objects_gt0_pass_gt0=FINAL_VCALL_REACHED',
'cpk_bind=0 main_patch=0 gameplay_patch=0 id_patch=0 path_rewrite=0 return_override=0',
]
for x in need:
    if x not in s: raise SystemExit(f'R265_SOURCE_VERIFY=FAIL missing_marker={x}')
if 'return nsc::InstallR265DownstreamRenderGateTrace();' not in core.read_text():
    raise SystemExit('R265_SOURCE_VERIFY=FAIL installer_not_selected')
if 'bool InstallR265DownstreamRenderGateTrace();' not in hpp.read_text():
    raise SystemExit('R265_SOURCE_VERIFY=FAIL declaration_missing')
ws=wf.read_text()
for x in ['verify_r265.py','NSC2Switch-R265-DOWNSTREAM-RENDER-GATE-TRACE']:
    if x not in ws: raise SystemExit(f'R265_SOURCE_VERIFY=FAIL workflow_marker={x}')
for bad in ['R265_PATH_REWRITE','R265_RETURN_OVERRIDE','R265_ID_PATCH','R265_FORCE_STATE']:
    if bad in s: raise SystemExit(f'R265_SOURCE_VERIFY=FAIL unsafe_marker={bad}')
print('R265_TARGET_SCOPE=mtobcharsel_native_id46')
print('R265_DRAW_SUBMIT=0x5B3AC')
print('R265_RENDER_OBJECT_GATE=0x43F1F8')
print('R265_READONLY=PASS')
print('R265_SOURCE_VERIFY=PASS')
