# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R92

## Current frontier
P89A admission bridge remains SOLVED and unchanged. Custom UJ reaches native BDC8=2/F58=true/action700 and progresses 700 -> 707 -> 708, but Kamui cinematic/hit-confirm handoff still sticks. Victim-side custom character remains safe under enemy UJ; Event236/P50 victim-safe behavior must remain untouched.

## P90A boot failure — root cause locked
P90A compiled/packaged correctly but failed during boot installation. Runtime log reached P89 READY and then aborted inside exlaunch hook trampoline allocation with `Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)`. Therefore P90A's two additional whole-function trampolines at 0x768E84 and 0x769A4C exhausted the available trampoline pool. This was an instrumentation-budget failure, not a gameplay/cinematic crash and not a P89 failure.

## P90B architecture
P90B is the boot-safe replacement for P90A.
- Parent is exactly the proven P89A path.
- ZERO additional hook/trampoline installations.
- Reuses the already-installed P50 PlayAction trampoline at 0x766B8C.
- Existing PlayAction callback is enriched only with read-only snapshots for UJ-range actions 700..740.
- New marker: `[NSC:P90B] HANDOFF ... index=... caller_off=... action=... ea4=... bda4=... bdc8=... zero_extra_trampoline=1`.
- READY explicitly reports `zero_extra_trampolines=1`.
- No hooks at 0x768E84 or 0x769A4C.
- No dispatcher hook and no virtual BLR replay.

## Why P90B advances the investigation
P90C static proof established the 707/708 corridor around 0x7E47B8. Native code selects 707 with 708 fallback/transition logic, requests flow through 0x766B8C, and the handler uses actor+EA4. P90B captures EA4/BDA4/BDC8 at that proven action-request boundary without consuming another trampoline.

## Runtime test matrix
1. Vanilla connected UJ that completes cinematic.
2. Custom Kamui connected UJ until it sticks.
Prefer same opponent/conditions. Send full uzuy log.

Compare action sequence 700/707/708 and later 709/710/711/712/713/714/740, caller_off, action pre/post, EA4 pre/post, and BDA4/BDC8 pre/post. Goal remains the FIRST divergence after P89 admission.

## Non-negotiable rules retained
Generic/data-driven only; Tobi/281 is fixture only. No char281 gameplay branch. No force700/708, action445 rewrite, BDC8/F58/EA4 write, selector8 workaround, raw Event236 restoration, victim-side changes, or manual mid-function BLR replay.

## Build-kit rule
P90B is P40-style drop-in: extract into repo root, overwrite, git add/commit/push. No APPLY.py or manual source repair. Only `build-subsdk9-p90b.yml` has a push trigger; P87/P88/P89 workflows are manual-only.

## Fingerprints
Program ID: 0100FA10190A0000
Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## Immediate next action
Build P90B in GitHub Actions. Audit compiled artifact before runtime test. If it boots, collect vanilla-complete + custom-stuck traces and compare P90B HANDOFF records.
