from pathlib import Path
b=Path('overlay/source/program/nsc_cpk_bridge.cpp').read_text()
c=Path('overlay/source/program/nsc_runtime_core.cpp').read_text()
h=Path('overlay/source/program/nsc_cpk_bridge.hpp').read_text()
w=Path('.github/workflows/build-runtime-r181.yml').read_text()
checks={
 'core_calls_r204p_only':'return nsc::InstallR204PPreambleStateTrace();' in c,
 'public_decl':'bool InstallR204PPreambleStateTrace();' in h,
 'ready_marker':'[NSC:R204P] READY' in b and 'trampoline_count=4' in b and 'preamble_state=1' in b,
 'process':'LoadRequestProcessHook::InstallAtOffset(kLoadRequestProcessOffset);' in b,
 'file_open':'FileOpenHook::InstallAtOffset(kFileOpenOffset);' in b,
 'read_dispatch':'FileReadDispatchHook::InstallAtOffset(kFileReadDispatchOffset);' in b,
 'read_stage':'ReadStageHook::InstallAtOffset(kReadStageOffset);' in b,
 'preamble_ctx':'[NSC:R204P] PREAMBLE_CTX' in b and 'q1c8' in b,
 'preamble_local':'[NSC:R204P] PREAMBLE_LOCAL' in b,
 'workflow_verifier':'python3 verify_r204p.py' in w,
 'workflow_artifact':'NSC2Switch-R204P-NATIVE-READ-STAGE-PREAMBLE-TRACE' in w,
}
# Only 4 hooks are installed in InstallTraceHooks focused block.
section=b[b.index('// R204P preamble-state control'):b.index('bool InstallP52PreUjTraceHooks()')]
for forbidden in ['StreamAttachHook::InstallAtOffset','StreamReadHook::InstallAtOffset','ReadHeaderHook::InstallAtOffset','ReadPayloadHook::InstallAtOffset','ReadFinalHook::InstallAtOffset']:
 checks['omits_'+forbidden.split('::')[0]]=forbidden not in section
for name,off in [('PROCESS','0x116F404'),('FILE_OPEN','0x1170FB0'),('READ_DISPATCH','0x11705F0'),('READ_STAGE','0x120A860')]:
 checks['offset_'+name]=off in b
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('R204P_SOURCE_VERIFY=FAIL '+','.join(failed))
print('R204P_SOURCE_VERIFY=PASS')
for k in checks: print(f'{k}=PASS')
