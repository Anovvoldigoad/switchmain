# NSC Runtime V2O — Native StageInfo Reindex on Registry Miss

Baseline: V2N/V2K. UJ admission, D-pad, voice and generic SFX are unchanged.

V2N hardware proof:
- custom `STG_2TOB_UNI_LT` key `0x01D1CA7E`: registry miss (`found=0`) before and after StageSpecific.
- vanilla restore `STAGE_SI45A` key `0x2BCB5498`: registry hit (`found=1`).

V2O performs one generic controlled A/B on the first real stage-key miss after the extra mod CPK binds successfully:
1. Resolve the native StageInfo manager from the exact StageSpecific chain `runtime_root -> +0x6C10 -> +0x148`.
2. Call the game's own v1.70 StageInfo reload entry `main+0x835FAC` once.
3. The native loader reads `data/stage/StageInfo.bin.xfbin` and `AdvStageInfo.bin.xfbin`, uses the native parser/descriptor builder, and native duplicate handling/insertion.
4. Re-probe the requested key.
5. If found, normal StageSpecific proceeds and sees the descriptor. If still missing, behavior remains fail-closed/baseline.

No hand-built descriptor, no manual PostStage, no char281 gameplay branch, no D-pad/voice/P128 changes.

Key marker:
`[NSC:V2O] STAGE_REINDEX ... before_found=0 after_found=0/1 ...`

Expected decisive outcomes:
- `after_found=1`: runtime registration gap repaired through the native loader; inspect resulting environment/resource requests and visual stage.
- `after_found=0`: mounted CPK does not expose a usable custom StageInfo record to the native loader; fix packaging/semantic StageInfo merge instead of adding more runtime lifecycle calls.
