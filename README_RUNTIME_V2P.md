# NSC2Switch Runtime V2P — StageInfo/CPK Passive Ordering Probe

This is a **standalone full source drop-in**. You do NOT need V2O source.

## What V2P does

V2P is built from the last recoverable full source baseline and keeps the stage-critical proven line:
- original v1.70 `main` on disk;
- V2D runtime resolver + exact 30-word patch;
- P128 UJ admission/session path;
- V2H safe opcode23 suppression;
- V2I stage actor+enemy parity, no manual PostStage;
- V2I generic opcode26 SFX playback;
- V2M safe stage/resource tracing;
- V2N read-only native StageInfo registry proof.

V2P adds only passive ordering markers around the already-existing file-load and CPK-bind callbacks.
It does **not** call `main+0x835FAC`, does not reindex StageInfo, does not insert descriptors, and adds no StageInfo-loader trampoline.

## Build — easiest GitHub method

1. Extract this ZIP.
2. Put the **contents** of the extracted folder at the root of a GitHub repo.
   You should see `.github/`, `overlay/`, `original/`, `reference_p128/`, `prepare_exlaunch.sh`, and `verify_runtime_v2p.py` at repo root.
3. Commit/push to `main`.
4. Open GitHub -> **Actions** -> **Build NSC Runtime V2P StageInfo CPK Passive Ordering Probe**.
5. If push did not start it automatically, press **Run workflow**.
6. Wait for the workflow to pass.
7. Download artifact: `NSC-RUNTIME-V2P-stageinfo-cpk-order-probe`.

The workflow packages:
- `atmosphere/contents/0100FA10190A0000/exefs/main` (locked original v1.70 main)
- `atmosphere/contents/0100FA10190A0000/exefs/subsdk9` (new V2P runtime)
- restore copy of original main
- SHA256SUMS.txt

Install that runtime artifact the same way as the previous V2N/V2O runtime artifact.

## Optional local source verification

Before pushing/building:

```bash
python3 verify_runtime_v2p.py
```

Expected final line:

```text
NSC_RUNTIME_V2P_SOURCE_VERIFY=PASS
```

## Hardware/emulator test — only this sequence

1. Fresh boot.
2. Do NOT press D-pad.
3. Select Tobi.
4. Enter battle normally.
5. Use Tobi own UJ exactly once.
6. Let the cinematic/failed stage transition run long enough to return if it can.
7. Save/close and immediately keep the full Uzuy log.
8. Upload the full log **and the compiled V2P runtime artifact** for analysis.

## Markers to look for

Boot:
```text
[NSC:V2P] READY stageinfo_cpk_order_probe=1 passive_only=1 ...
[NSC:V2N] READY stage_registry_probe=1 ...
[NSC:V2M] READY stage_only=1 installed=1 ...
```

Natural StageInfo load:
```text
[NSC:V2P] STAGEINFO_LOAD_REQ phase=pre ... path=data/stage/StageInfo.bin.xfbin cpk_bound=0/1 ...
[NSC:V2P] STAGEINFO_LOAD_REQ phase=post ... cpk_bound_pre=0/1 cpk_bound_post=0/1 ...
```

Extra mod CPK bind:
```text
[NSC:V2P] CPK_BOUND ... success=1 stageinfo_seen_before_bind=0/1 ...
```

UJ registry proof:
```text
[NSC:V2N] STAGE_REGISTRY phase=pre_specific text=STG_2TOB_UNI_LT key=01d1ca7e ... found=0/1 ...
```

## Interpretation

- `StageInfo cpk_bound=0` then later `CPK_BOUND success=1`, and UJ registry still `found=0`:
  **ordering bug is strongly supported** — native StageInfo initialization happened before the custom CPK became visible.

- `StageInfo cpk_bound=1`, but UJ registry `found=0`:
  bind timing is not the main problem; inspect **StageInfo packaging/merge semantics**.

- UJ registry `found=1` but visual battle map still mixes:
  move downstream to descriptor/environment/resource lifecycle; do not touch P128 admission.

- No StageInfo markers at all but V2P READY appears:
  the existing file-load boundary did not observe natural StageInfo initialization; next probe must move to the native init caller boundary, still passively.

## Locked safety rules

Do not re-add V2O runtime reindex. Do not call `main+0x835FAC` manually from Event236.
Do not manually build/insert StageInfo descriptors. Do not re-add V2J manual PostStage.
Do not modify P128, raw15 admission, visibility, global damage, or D-pad while testing this stage-order frontier.
