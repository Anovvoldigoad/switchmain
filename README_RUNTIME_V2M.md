# NSC2Switch Runtime V2M — Stage Safe Resource/Environment Trace

V2M is a diagnostic-only stage build based directly on the hardware-stable V2K baseline.

## Purpose
The current Tobi UJ reaches action 710 and `STG_2TOB_UNI_LT` changes the live stage ID, but battle-map geometry remains mixed with the Kamui cinematic. V2M traces the resource/environment boundary without changing stage behavior.

## Important correction from V2L
Do **not** use V2L. Static review found that V2L reused pre-transition object pointers for post-transition logging. V2M re-resolves the stage graph fresh after each transition boundary and only logs pointer identity.

## New markers
- `[NSC:V2M] READY ...`
- `[NSC:V2M] STAGE_TRACE_ARM ...`
- `[NSC:V2M] STAGE_GRAPH phase=pre_specific|post_specific|post_handle|post_fix ...`
- `[NSC:P50A] LOAD_REQ ...`
- `[NSC:P50A] FILE_OPEN ...`
- `[NSC:P50A] STAGE_HANDLE ...`
- `[NSC:P50A] POST_STAGE ...` (observation only)
- `[NSC:V2M] STAGE_TRACE_DISARM ...`

## Test
Fresh boot -> Tobi -> do not use D-pad -> Tobi UJ once -> let it return to battle -> save full log.

## Packaging
The GitHub Actions artifact contains the original v1.70 `main` plus compiled `subsdk9`.
