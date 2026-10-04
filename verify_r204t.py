#!/usr/bin/env python3
from pathlib import Path
import re
root=Path(__file__).resolve().parent
b=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
c=(root/'overlay/source/program/nsc_runtime_core.cpp').read_text()
h=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
w=(root/'.github/workflows/build-runtime-r181.yml').read_text()
checks={
 'core_calls_r204t_only':'return nsc::InstallR204TTargetOnlyStreamForensicTrace();' in c,
 'public_decl':'bool InstallR204TTargetOnlyStreamForensicTrace();' in h,
 'ready_marker':'[NSC:R204T] READY' in b and 'boot_safe=1' in b and 'trampoline_count=9' in b and 'target_only=1' in b,
 'process_path_map':'PROCESS_ENTER' in b and 'TrackRequestPath(read_context, path)' in b,
 'file_open':'FileOpenHook::InstallAtOffset(kFileOpenOffset);' in b,
 'read_dispatch':'FileReadDispatchHook::InstallAtOffset(kFileReadDispatchOffset);' in b and '[NSC:R204T] READ_DISPATCH_ENTER' in b,
 'read_stage':'ReadStageHook::InstallAtOffset(kReadStageOffset);' in b and '[NSC:R204T] READ_STAGE_ENTER' in b,
 'stream_attach':'StreamAttachHook::InstallAtOffset(kStreamAttachOffset);' in b and '[NSC:R204T] STREAM_ATTACH_ENTER' in b,
 'stream_read':'StreamReadHook::InstallAtOffset(kStreamReadOffset);' in b and '[NSC:R204T] STREAM_READ_ENTER' in b,
 'read_header':'ReadHeaderHook::InstallAtOffset(kReadHeaderOffset);' in b and '[NSC:R204T] READ_HEADER_ENTER' in b,
 'read_payload':'ReadPayloadHook::InstallAtOffset(kReadPayloadOffset);' in b and '[NSC:R204T] READ_PAYLOAD_ENTER' in b,
 'read_final':'ReadFinalHook::InstallAtOffset(kReadFinalOffset);' in b and '[NSC:R204T] READ_FINAL_ENTER' in b,
 'workflow_verifier':'python3 verify_r204t.py' in w,
 'workflow_artifact':'NSC2Switch-R204T-NATIVE-PER-RESOURCE-STREAM-FORENSIC' in w,
 'no_old_verifier':'verify_r204n.py' not in w,
 'no_cpk_bind_install':'CpkBindHook::Install' not in b[b.index('bool InstallR204TTargetOnlyStreamForensicTrace()'):b.index('bool InstallPlayActionProbe()')],
}
# Count only InstallAtOffset calls inside InstallTraceHooks function body.
start=b.index('bool InstallTraceHooks()')
end=b.index('bool InstallP52PreUjTraceHooks()',start)
segment=b[start:end]
installs=re.findall(r'([A-Za-z0-9_]+Hook)::InstallAtOffset',segment)
expected=['LoadRequestProcessHook','FileOpenHook','FileReadDispatchHook','ReadStageHook','StreamAttachHook','StreamReadHook','ReadHeaderHook','ReadPayloadHook','ReadFinalHook']
checks['focused_install_count']=len(installs)==9
checks['focused_install_exact']=installs==expected
# Fingerprint constants must remain present.
for name,off in [('PROCESS','0x116F404'),('FILE_OPEN','0x1170FB0'),('READ_DISPATCH','0x11705F0'),('READ_STAGE','0x120A860'),('STREAM_ATTACH','0x118819C'),('STREAM_READ','0x11882AC'),('READ_HEADER','0x120A99C'),('READ_PAYLOAD','0x120AA5C'),('READ_FINAL','0x120B35C')]:
    checks['offset_'+name]=off in b

checks.update({
 'target_filter_excludes_mtobprm':'BoundedContains(path, "mtobprm_load"' not in b[b.index('bool IsR204TDeepReadTargetPath'):b.index('const char* LoadOwnerPath')],
 'stream_forensic_fields':all(x in b for x in ['bufptr=%p','read_method_off=0x%lx','wait=%p','state=%u','size=%u','pos=%u']),
 'per_resource_stream_quota':all(x in b for x in ['g_stream_read_control_logs','g_stream_read_bod1_logs','g_stream_read_bod1acc_logs','TakeR204TStreamLogSlot','limit = 24','limit = 1024']),
 'paired_enter_exit_same_slot':'const bool log_this = interesting && TakeR204TStreamLogSlot(stream_class, &seq);' in b and 'STREAM_READ_ENTER seq=%u class=%u' in b and 'STREAM_READ_EXIT seq=%u class=%u' in b,
})

failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(f'{k}={"PASS" if v else "FAIL"}')
if failed: raise SystemExit('R204T_SOURCE_VERIFY=FAIL '+','.join(failed))
print('R204T_SOURCE_VERIFY=PASS')
