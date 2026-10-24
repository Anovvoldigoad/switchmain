# VERIFIED HISTORICAL PAIRED-MAIN CANDIDATE: P128A
Date: 24 October 2026 (forensic index). Base commit: `6cf1d4292ccdf5cf35593f3b606e14963eb23f0d`. Executable sources and original P128A workflow are preserved byte-for-byte on this branch.

## Decisive outcome — post-build hardware evidence, not CI only

The later R181 master checkpoint's **Section 14: "P128A — decisive UJ admission success"** explicitly records:
- Tobi own UJ **enters cinematic**.
- Tobi **can move after UJ**.
- Naruto UJ **safe**.
- Tobi as enemy-UJ victim **safe**.
- Native cinematic session works.

It labels P128A *the first fully useful functional UJ checkpoint*.

Source:
https://github.com/Anovvoldigoad/switchmain/blob/df65ebeee6f7/NSC2Switch_MASTER_CHECKPOINT_2026-09-30_R181_FULL.md

**Important correction**: `README_P128A.txt` and `NSC2Switch_MASTER_CHECKPOINT_2026-09-26_R144.md` describe conditions **before P128A gameplay testing**: Tobi own UJ still stuck in P127; that historical pretest finding does **not** contradict the later posttest P128A hardware success recorded by R181. Do not classify P128A as UJ FAIL based on the earlier README alone.

## Exact artifact / main lineage

- GitHub Actions run: https://github.com/Anovvoldigoad/switchmain/actions/runs/36240507170
- GitHub artifact name: `NSC-P128A-static-precise-gate-cave-proof`.
- GitHub artifact ID: `10904639165`, unexpired on audit.
- Exact patched `main` is packaged at `atmosphere/contents/0100FA10190A0000/exefs/main` with `subsdk9` beside it. The archive includes separate `restore/.../exefs/main`.
- Patched main SHA-256: `904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff`.
- Original Switch 1.70 main SHA-256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- Source and workflow under `6cf1d4292ccdf5cf35593f3b606e14963eb23f0d`.

This is the strongest grounded match to the user's memory of a tested **patched main + subsdk9** Tobi character with functional UJ.

## Limits of the recovered baseline

- P128A posttest residual defects are documented: Kamui cinematic environment still mixes with the battle stage, and voice/audio parity is incomplete.
- Later R164 StageInfo **hardware PASS** and R172 UJ animation fix **hardware PASS** are subsequent milestones. Do not treat them as already present in the P128A ZIP.
- The **specific True Awakening** feature the user remembers remains not independently confirmed by the P128A / R181 documents, which distinguish an `OugiAwakening` policy hook (necessary for UJ) from fully validated transformation gameplay. The user's report is retained as a relevant lead, not denied.
- The P128A Actions artifact is an **ExeFS package**, not the full 93-resource RomFS carrier. Runtime+asset pairing matters; never interpret P128A alone as a standalone character mod.
- Do not mix P128A's already-patched `main` with V2D/R172/R181 `subsdk9`, which expects to validate **original** prepatch instructions before writing its 30-word runtime patch (fails closed if already prepatched).
- Do not install the old patched main over a current setup without keeping a backup; it is locked to Switch 1.70 signatures and is not update-resilient.

## Precise recovery approach

1. Treat this paired P128A artifact, not R183 or minimal P32/34/37/38/39, as the most accurate historical **UJ + patched-main reference**.
2. Recover the **same historical CPK, StageInfo, UI, and native runtime build** from the contemporary test if available; a modern P37 carrier is not evidence of data parity.
3. Compare Tobi battle/True Awakening with old paired executable and matched historical assets **in a reversible test**, and log exact original/patched-main SHA before invoking any later runtime build.
4. Restore full playable features first. Only after a matching measured result, migrate **one** dependency to a version-agnostic resolver and verify no functional regression.
