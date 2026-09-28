# NSC2Switch Runtime V2L — Stage Resource / Environment Trace

Target: Storm Connections Switch v1.70, Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`.

Original main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.

## Purpose
V2L freezes V2K gameplay behavior and investigates only the remaining Tobi UJ stage bug: `STG_2TOB_UNI_LT` is accepted and the live stage ID changes, but normal battle-map geometry remains visible during the Kamui cinematic.

## What changes
- No StageMove behavior change.
- No manual `0x48E61C` / PostStage call.
- No D-pad changes.
- No voice changes.
- No P128/UJ-admission changes.
- Adds read-only stage object-graph snapshots at pre-specific, post-specific, post-HandleStageChange, and post-position-fix boundaries.
- Adds read-only resource request + file-open tracing for stage-related assets. During the first custom StageMove the trace widens to XFBIN/stage paths and stays active until the second custom StageMove (normally entry -> return).
- Adds read-only hooks around native HandleStageChange and PostStage to detect actual native call order; V2L never calls PostStage itself.

## Key markers
- `[NSC:V2L] READY ... gameplay_write=0`
- `[NSC:V2L] STAGE_TRACE_ARM ...`
- `[NSC:V2L] STAGE_GRAPH phase=pre_specific|post_specific|post_handle|post_fix ...`
- `[NSC:P50A] LOAD_REQUEST ...`
- `[NSC:P50A] FILE_OPEN ... result=...`
- `[NSC:P50A] STAGE_HANDLE phase=0|1 ...`
- `[NSC:P50A] POST_STAGE phase=0|1` (only if the game itself invokes it)
- `[NSC:V2L] STAGE_TRACE_DISARM ...`

## Test
Fresh boot. Use Tobi UJ once and let the full cinematic finish. Do not test D-pad in this run. Save the full emulator log.

## Interpretation
1. Kamui resources never requested -> stage-data/resource registration/loading gap.
2. Resources requested but FILE_OPEN returns 0 -> asset path/bind/packaging gap.
3. Resources open successfully but stage graph remains owned by old environment -> environment lifecycle/rebind gap.
4. Native POST_STAGE appears automatically -> compare its timing instead of manually forcing it.
5. No native POST_STAGE appears -> do not infer it is required; V2J already proved forcing it is unsafe.
