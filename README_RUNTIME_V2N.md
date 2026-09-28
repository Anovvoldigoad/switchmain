# NSC2Switch Runtime V2N — Stage Registry Proof

Base: V2M/V2K stable stage path.

Purpose: prove whether the requested StageMove ID exists in the native Switch stage descriptor registry used by `main+0x535FBC`.

Static v1.70 chain:
- `main+0x536074` loads `[runtime_root+0x6C10]`
- `main+0x53607C` loads its `+0x148` registry map
- `main+0x536080` calls `main+0x8364F8(map, stage_id)`
- `main+0x536084` branches around environment setup when result is null

V2N duplicates that lookup read-only immediately before and after StageSpecific and logs `[NSC:V2N] STAGE_REGISTRY ... found=0/1`.

No registry insertion, no descriptor mutation, no stage-state write, no PostStage call, no D-pad/voice/P128 changes.

Expected diagnostic:
- custom `STG_2TOB_UNI_LT` miss + vanilla `STAGE_SI45A` hit => missing custom stage runtime registration is proven.
- both hit => inspect descriptor contents/stageFilter/environment setup next.
