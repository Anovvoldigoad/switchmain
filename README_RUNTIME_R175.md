# NSC2Switch R175 — D-pad Action Lookup Matrix Trace

Parent: hardware-tested R174 selector/fallback trace.

## Why R175 exists
R174 hardware separates the two clean D-pad runs before the fallback:
- one run: active_mode=2, base_candidate=921, actual PlayAction=921, fallback921_suspect=0;
- the other: active_mode=3, base_candidate=922, actual PlayAction=921, fallback921_suspect=1.

Therefore direction selection is not collapsed. The remaining boundary is the native action descriptor resolver `main+0x768E84(actor,index,flag)`.

## R175 behavior
R175 adds no hook/trampoline and performs no gameplay write. It reuses the existing PlayAction hook. On the first custom-actor route call at caller `0x646CFC` / actual 921 it re-queries the native resolver for actions 921..924 with:
- flag=1: exact native controller contract;
- flag=0: comparison path to detect a flag/remap-only gap.

Marker:
`[NSC:R175] ACTION_LOOKUP_MATRIX ...`

Key fields:
- active_mode / base_candidate
- f1_921..f1_924
- f0_921..f0_924
- candidate_f1 / candidate_f0
- native_candidate_missing
- flag1_only_gap
- state_changed

Expected decisions:
- candidate922 f1=null and f0=null -> descriptor genuinely absent/unresolvable for this actor.
- candidate922 f1=null but f0!=null -> compatibility gap is in flag=1 normalization/remap.
- candidate922 f1!=null while actual still 921 -> fallback hypothesis needs refinement below the branch.
- state_changed must remain 0.

Frozen:
- R172 UJ direct-animation fix
- exact P128 30-word runtime delta
- R164 StageInfo-fixed asset
- stage probes
- voice skipped/frozen
- no char281 gameplay branch

Build artifact:
`NSC-RUNTIME-R175-dpad-action-lookup-matrix-trace`
