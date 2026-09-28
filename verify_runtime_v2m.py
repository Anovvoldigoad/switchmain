from pathlib import Path
import hashlib, re, struct, sys
R=Path(__file__).resolve().parent
cpp=(R/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(R/'overlay/source/program/main.cpp').read_text()
hdr=(R/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
prep=(R/'prepare_exlaunch.sh').read_text()
wf=(R/'.github/workflows/build-runtime-v2m.yml').read_text()
checks={
'v2k_baseline': '[NSC:V2K] READY recovery_baseline=V2I' in cpp,
'v2m_main_call': 'InstallV2MStageSafeTraceHooks' in main and 'InstallV2MStageSafeTraceHooks' in hdr,
'v2m_ready': '[NSC:V2M] READY stage_only=1 installed=1' in cpp,
'fresh_graph_resolve': 'V2MResolveStageGraph' in cpp and 'fresh_resolve=1 stale_pointer_deref=0' in cpp,
'no_v2l_unsafe_q': 'V2LLogStageGraph' not in cpp and 'q(stage_global' not in cpp,
'four_graph_phases': all(x in cpp for x in ['"pre_specific"','"post_specific"','"post_handle"','"post_fix"']),
'resource_window': 'g_v2m_stage_asset_trace_active' in cpp and 'STAGE_TRACE_ARM' in cpp and 'STAGE_TRACE_DISARM' in cpp,
'failure_disarm': 'STAGE_TRACE_DISARM_FAIL' in cpp,
'load_request_trace': 'FileLoadRequestHook::InstallAtOffset(kFileLoadRequestOffset)' in cpp,
'file_open_trace': 'FileOpenHook::InstallAtOffset(kFileOpenOffset)' in cpp,
'handle_observe': 'StageHandleHook::InstallAtOffset(kHandleStageChangeOffset)' in cpp,
'post_observe_only': 'PostStageHook::InstallAtOffset(kPostStageOffset)' in cpp and 'manual_poststage_call=0' in cpp,
'no_v2j_post_call': 'reinterpret_cast<PostFn>(base + kPostStageOffset)();' not in cpp,
'op23_safe_retained': 'OP23_SAFE_SUPPRESS' in cpp and 'call_766320=0 playaction_wrapper=0' in cpp,
'op26_retained': 'OP26_PLAY' in cpp,
'p128_retained': '[NSC:P128A] READY' in cpp,
'workflow_v2m': 'verify_runtime_v2m.py' in wf and 'NSC-RUNTIME-V2M-stage-safe-resource-environment-trace' in wf,
'workflow_original_main': 'cp original/atmosphere/contents/0100FA10190A0000/exefs/main "$EXE/main"' in wf,
'prepare_v2m_elf': 'runtime_v2m.elf' in prep,
'no_char281_branch': 'if (char_id == 281' not in cpp and 'if (char == 281' not in cpp,
}
for k,v in checks.items(): print(k, 'PASS' if v else 'FAIL')
if not all(checks.values()): sys.exit(1)
orig=R/'original/atmosphere/contents/0100FA10190A0000/exefs/main'
ref=R/'reference_p128/atmosphere/contents/0100FA10190A0000/exefs/main'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
so,sr=sha(orig),sha(ref)
print('original_main_sha256',so)
print('reference_p128_main_sha256',sr)
if so!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9': sys.exit(2)
if sr!='904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff': sys.exit(3)
try:
    import lz4.block
except Exception:
    lz4=None

def decode_text(path):
    b=path.read_bytes()
    if b[:4] != b'NSO0':
        raise RuntimeError('not NSO0: '+str(path))
    u=lambda o:struct.unpack_from('<I',b,o)[0]
    flags=u(0x0c); fo=u(0x10); va=u(0x14); size=u(0x18); csz=u(0x60)
    blob=b[fo:fo+(csz if flags&1 else size)]
    if flags&1:
        if lz4 is None: raise RuntimeError('lz4 required')
        blob=lz4.block.decompress(blob,uncompressed_size=size)
    return va,blob

va_o,a=decode_text(orig); va_r,b=decode_text(ref)
if va_o!=0 or va_r!=0 or len(a)!=len(b): sys.exit(4)
diff={off:(struct.unpack_from('<I',a,off)[0],struct.unpack_from('<I',b,off)[0])
      for off in range(0,len(a)-3,4)
      if struct.unpack_from('<I',a,off)[0]!=struct.unpack_from('<I',b,off)[0]}
print('text_diff_words',len(diff))
expected={
0x747878:(0x52804009,0x528040A9),
0x7774DC:(0x7108031F,0x7108171F),
0x777770:(0x7108027F,0x7108167F),
0x777938:(0x7108027F,0x7108167F),
0x777A6C:(0x7108027F,0x7108167F),
0x7F2A9C:(0xBD001FE0,0xD503201F),
0x77C480:(0x54000B81,0x1400000E),
0x77C494:(0x34000AC0,0xD503201F),
0x77C4A8:(0x34000A20,0xD503201F),
0x77C4B4:(0x34000300,0x14000018),
0x77C4B8:(0xF0009619,0x7100291F),0x77C4BC:(0x913C2339,0x54000220),
0x77C4C0:(0xAA1903E0,0x71002D1F),0x77C4C4:(0x942A6437,0x540001E0),
0x77C4C8:(0xF9400268,0x71003D1F),0x77C4CC:(0xAA1303E0,0x54000181),
0x77C4D0:(0xF9402508,0xB94E56EA),0x77C4D4:(0xD63F0100,0x7104615F),
0x77C4D8:(0x11000401,0x54000129),0x77C4DC:(0xB0009680,0x7140055F),
0x77C4E0:(0x91292C00,0x540000E2),0x77C4E4:(0x942A642F,0xF9410EEA),
0x77C4E8:(0xF94002E8,0xB40000AA),0x77C4EC:(0xAA1703E0,0xB9402D4A),
0x77C4F0:(0xF9402508,0x710B0D5F),0x77C4F4:(0xD63F0100,0x54000041),
0x77C4F8:(0x11000401,0x14000002),0x77C4FC:(0xB0009940,0x1400003D),
0x77C500:(0x91086800,0x17FFFFE1),
0x77C520:(0xB40003E0,0x1400001F),
}
if diff!=expected:
    print('reference_delta_exact_30_words FAIL',len(diff));sys.exit(5)
print('reference_delta_exact_30_words PASS')
print('NSC_RUNTIME_V2M_SOURCE_VERIFY=PASS')
