#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parent
cpp=root/'overlay/source/program/nsc_cpk_bridge.cpp'
core=root/'overlay/source/program/nsc_runtime_core.cpp'
hpp=root/'overlay/source/program/nsc_cpk_bridge.hpp'
wf=root/'.github/workflows/build-runtime-r181.yml'
for p in [cpp,core,hpp,wf]:
    if not p.is_file(): raise SystemExit(f'R266_SOURCE_VERIFY=FAIL missing={p}')
s=cpp.read_text()
need=[
'kR266ModelChildCreateOffset       = 0x6ECEE8',
'kR266RegistrationTickOffset       = 0x6ED558',
'kR266RegistrationBridgeOffset     = 0x6ED110',
'kR266RenderProducerOffset         = 0x594D8',
'kR266RenderProducerGuardOffset    = 0x5E998',
'R266ModelChildCreateHook','R266RegistrationTickHook','R266RegistrationBridgeHook',
'R266RenderProducerHook','R266RenderProducerGuardHook',
'MODEL_CHILD_CREATE','REG_TICK_PRE','REG_BRIDGE','RENDER_PRODUCER_PRE','PRODUCER_GUARD',
'child_count0=MODEL_REG_CHILD_VECTOR_EMPTY','count_gt0_no_bridge=CHILD_READINESS_BLOCK',
'bridge_no_producer=BRIDGE_RESOURCE_OR_MANAGER_BLOCK','producer_guard0=PRODUCER_GUARD_BLOCK',
'producer_guard1_submit_empty=POST_GUARD_INDEX_OR_FILL_BLOCK',
'hooks=11','cpk_bind=0 main_patch=0 gameplay_patch=0 id_patch=0 path_rewrite=0 return_override=0',
]
for x in need:
    if x not in s: raise SystemExit(f'R266_SOURCE_VERIFY=FAIL missing_marker={x}')
core_s=core.read_text()
if 'return nsc::InstallR266RenderRegistrationProducerTrace();' not in core_s:
    raise SystemExit('R266_SOURCE_VERIFY=FAIL installer_not_selected')
if 'bool InstallR266RenderRegistrationProducerTrace();' not in hpp.read_text():
    raise SystemExit('R266_SOURCE_VERIFY=FAIL declaration_missing')
ws=wf.read_text()
for x in ['verify_r266.py','NSC2Switch-R266-RENDER-REGISTRATION-PRODUCER-TRACE']:
    if x not in ws: raise SystemExit(f'R266_SOURCE_VERIFY=FAIL workflow_marker={x}')
for bad in ['R266_PATH_REWRITE','R266_RETURN_OVERRIDE','R266_ID_PATCH','R266_FORCE_STATE']:
    if bad in s: raise SystemExit(f'R266_SOURCE_VERIFY=FAIL unsafe_marker={bad}')
# Original main authority must stay bundled for compile/reference parity.
main=root/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
if not main.is_file(): raise SystemExit('R266_SOURCE_VERIFY=FAIL original_main_missing')
import hashlib
sha=hashlib.sha256(main.read_bytes()).hexdigest()
if sha!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9':
    raise SystemExit(f'R266_SOURCE_VERIFY=FAIL original_main_sha={sha}')
print('R266_TARGET_SCOPE=native_id46_render_registration')
print('R266_MODEL_CHILD_CREATE=0x6ECEE8')
print('R266_REGISTRATION_TICK=0x6ED558')
print('R266_REGISTRATION_BRIDGE=0x6ED110')
print('R266_RENDER_PRODUCER=0x594D8')
print('R266_PRODUCER_GUARD=0x5E998')
print('R266_READONLY=PASS')
print('R266_SOURCE_VERIFY=PASS')
