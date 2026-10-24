# NSC2Switch restoration audit — R183 full runtime before minimal-loader investigation
**Audit date:** 24 October 2026. **Branch parent:** `460b7ff384d41c1b77f1814c9fb5550604baafdc` (R183). No executable gameplay source has been edited on this recovery branch.

## Coverage of GitHub Actions
Enumerated all 372 GitHub Actions runs visible in `Anovvoldigoad/switchmain` from 15 September to 24 October 2026: 275 succeeded and 97 failed. This is **workflow execution status, not gameplay verification**. Artifacts and source trees were examined for key restoration milestones, not 372 downloaded ZIPs.

## What the historic evidence actually supports
| Date | Run | Artifact | Verified meaning |
| ---- | --- | -------- | ---------------- |
| 26 Sep | [P128A](https://github.com/Anovvoldigoad/switchmain/actions/runs/36240507170) | `NSC-P128A-static-precise-gate-cave-proof` | paired main and subsdk9; source/CI gate cave build (not a stand-alone playable claim) |
| 26 Sep | [V2D](https://github.com/Anovvoldigoad/switchmain/actions/runs/36255430668) | `NSC-RUNTIME-V2D-original-main-runtime-patch` | bootstrap with original main + 30 RAM patch words to reproduce P128-compatible behavior |
| 29 Sep | [R172](https://github.com/Anovvoldigoad/switchmain/actions/runs/36528701882) | `NSC-RUNTIME-R172-uj-miss-anmdirect-parity` | R172 UJ confirmed hardware PASS in master checkpoint: no longer loops |
| 29 Sep | [R181](https://github.com/Anovvoldigoad/switchmain/actions/runs/36617484538) | `NSC-RUNTIME-R181-dpad-full-eligibility-rollback` | contains full runtime and historical gameplay lineage; checkpoint reports R164 StageInfo hardware PASS, R172 UJ hardware PASS, R181 Dpad rollback not necessarily PASS |
| 2 Oct | [R181 runtime core](https://github.com/Anovvoldigoad/switchmain/actions/runs/37036151909) | `NSC2Switch-RUNTIME-CORE-R181` | first ModdingAPI decoupling; changed binding and resolver semantics; R182 hardware later reported VS stall/Isshiki regression |
| 2 Oct | [R183](https://github.com/Anovvoldigoad/switchmain/actions/runs/37040185240) | `NSC2Switch-RUNTIME-R183-compat-hotfix` | restores R181 gameplay-sensitive paths, preserves bootstrap/core split; successful CI; **R183 hardware gameplay PASS not established** |
| 6 Oct | [R276H19C](https://github.com/Anovvoldigoad/switchmain/actions/runs/37485621289) | `NSC-R276H19C-minimal-binder` | intentionally minimal loader; no R183 gameplay initialization pipeline |
| 18–24 Oct | P32/P34/P37/P38/P39 | separate tracing and CPK-packaging artifacts | Tobi resource loads, but opponent invisibility persists; P38 observed zero model-registration callback markers |

## Crucial code evidence, not conjecture
R181 `overlay/source/program/main.cpp` calls:
```cpp
nsc::v2::InstallResolverHookMigrationProbe();
if (!nsc::v2::InstallOriginalMainRuntimePatches()) return;
if (!nsc::v2::InstallR181DpadFullEligibilityRollback()) return;
nsc::InstallP128AStaticPreciseGateCaveProof();
nsc::InstallR172UjMissAnmDirectParity();
nsc::InstallR175DpadLookupMatrixTrace();
nsc::InstallR176ActionRegistryMatrixTrace();
nsc::InstallR177ActionDescriptorMatrixTrace();
nsc::InstallV2NStageRegistryProof();
nsc::InstallV2PPassiveOrderProbe();
```
R183 moves this **same installation order** into `nsc_runtime_core.cpp` and calls `nsc_runtime_initialize()` from the exlaunch bootstrap. Its workflow packages **only subsdk9, no main override**, while `InstallOriginalMainRuntimePatches()` writes the fixed v1.70 30-word compatibility patch into main RAM after validating the target.
By contrast, the R276H19C entrypoint calls only `InstallMinimalCpkBridge()`, and P32/P34/P37–P39 only call `InstallP32Trace()`, which binds CPK and reads/observes XFBIN; they do not activate the R183 gameplay runtime. That is the proven, large functional gap.

Compare commit `460b7ff` → `e57afa5`: the native `nsc_cpk_bridge.cpp` loses **9,403 lines**, `nsc_runtime_core.cpp` and `nsc_runtime_v2.cpp` are removed. The P32 branch subsequently diverges, but likewise lacks the full runtime pipeline.

The R182 source architectural migration was genuinely regressive: source file `MODDINGAPI_R183_COMPAT_HOTFIX_REPORT.md` reports a new/custom character stuck at VS and Isshiki regression. It identifies a mandatory R181 initialization gate signature resolution failure as possible, plus ModPack-primary-vs-Tobi_CPK fallback binding. R183 restores the fixed R181 gate check, R172 setter check, and single Tobi_CPK path. It is **not proven by the report alone that R183 corrected every runtime issue**.

## True Awakening evidence boundary
The user reports their old installation supported True Awakening and UJ. This testimony is an important observation to preserve. However the R181 full checkpoint explicitly labels broad awakening parity **not yet complete** in an older section; its frozen hardware PASS is for R164 StageInfo and R172 UJ. Do not conflate an Action success state, R172 UJ success or generic P81 Ougi/Awakening hook with separately proven full True Awakening. Identify the specific former artifact and its matching CPK setup to reconcile the discrepancy.

## Restoration contract (strict)
1. **Use the full R183 runtime baseline**, not P32/P34/P38/P39 as gameplay base. This branch deliberately keeps original R183 source and one-shot bootstrap; it does not claim a new binary.
2. **Keep the proven R164-era StageInfo fixed carrier/data** (checkpoint names `Tobi_Switch_R164_STAGEINFO_FIXED.zip`) separate from the later experimental P37 93-entry carrier. The original R164 ZIP is not inside the R183 GitHub Actions runtime artifact. Do not silently mix versions.
3. Verify code and original Switch 1.70 build ID/SHA before installing; do not combine R183 bootstrap with a patched historical `main`, or claim game-update immunity from fixed-address signatures.
4. Establish a restorable runtime+asset baseline before converting **one** version-coupled native dependency to resolver-driven execution. Migrate P81/P89/P125 and StageInfo in isolation with test evidence.
5. Character packages can be RomFS-only **when the once-installed runtime bootstrap is present**. A mod which works with **no** executable bootstrap at all is a different, unproven architecture.
6. User's current symptom (opponent invisible) is not resolved by this audit. No return-value hacks, blanket visibility writes, or new random CPK payload rewrites are justified by current evidence.

**Current decision:** stop interpreting successful P34 file opens as gameplay integration. Preserve R183 as recovery anchor, recover matching R164 CPK state, and then validate actor visibility/True Awakening/UJ under the full native runtime. Do not merge this recovery line with P39 experimental rendering hooks until comparable runtime evidence exists.
