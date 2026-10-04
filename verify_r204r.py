from pathlib import Path
b=Path("overlay/source/program/nsc_cpk_bridge.cpp").read_text()
c=Path("overlay/source/program/nsc_runtime_core.cpp").read_text()
h=Path("overlay/source/program/nsc_cpk_bridge.hpp").read_text()
w=Path(".github/workflows/build-runtime-r181.yml").read_text()
checks={
 "core":"return nsc::InstallR204RRootCauseProbe();" in c,
 "decl":"bool InstallR204RRootCauseProbe();" in h,
 "ready":"[NSC:R204R] READY" in b and "trampoline_count=5" in b and "inline_breadcrumbs=9" in b,
 "ctx":"ReadContextAccessorHook::InstallAtOffset(kReadContextAccessorOffset);" in b,
 "breadcrumb":"[NSC:R204R] BREADCRUMB stage=%s" in b,
 "a1":"POST_ACCESSOR1" in b and "0x120A88C" in b,
 "tls":"POST_TLS1" in b and "0x120A89C" in b,
 "attach":"POST_STREAM_ATTACH" in b and "0x120A8AC" in b,
 "header":"POST_READ_HEADER" in b and "0x120A8B4" in b,
 "h1":"POST_HELPER_116B880" in b and "0x120A8CC" in b,
 "h2":"POST_HELPER_116AF60" in b and "0x120A8E8" in b,
 "h3":"POST_HELPER_12099C8" in b and "0x120A8F8" in b,
 "payload":"POST_READ_PAYLOAD" in b and "0x120A908" in b,
 "final":"POST_READ_FINAL" in b and "0x120A91C" in b,
 "workflow_verify":"python3 verify_r204r.py" in w,
 "workflow_artifact":"NSC2Switch-R204R-NATIVE-READ-STAGE-ROOT-CAUSE-PROBE" in w,
}
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit("R204R_SOURCE_VERIFY=FAIL "+",".join(failed))
print("R204R_SOURCE_VERIFY=PASS")
for k in checks: print(f"{k}=PASS")
