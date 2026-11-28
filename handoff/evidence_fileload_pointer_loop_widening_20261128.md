# FileLoad pointer-page unknown-bound loop widening

Date: 2026-11-28
Branch: port/full-api-v170
Parent for current revision: ba6e656ed45875bf16dc8690b5660aee14c301eb
State: PENDING_CI

## Primary-source recheck

- NSC-ModManager release 2.1.2.1: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1, tag commit 502c38d3ee832509f9ee3951b7d3339826538fec. XfbinParser.cs blob faf79d588fd8beb3f5761faebedd2252853b2f2b; SkillCustomizeParamModel.cs blob 6a891e237d27fdf01336f806dbef8767d609a304. Relevant files fetched at upstream main are byte-identical to the tag.
- NSC-Toolbox release 2.1.2.1: https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1, tag commit 789fe96f99cdaa77f952b90b563c6e3f49b6d697. XfbinParser.cs blob 86c63708edf2698b5bc1c2a54c0480cce014b525; SkillEditorModel.cs blob e165471682e4a7aed91094ef07f92df271f31639. Relevant parser/editor files are byte-identical to upstream main.
- UltimateStormAPI 2.1.2.1: https://github.com/TheLeonX/UltimateStormAPI/blob/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc/xinput9_1_0/MovesetPlus.cpp; commit a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc, blob d7c5dbbebd60415f8d304321f083897658a86146. Command 29 is PC Windows mutex/timing behavior, not Switch ABI.
- PyCriCodecs commit 755055ee7b056c9c1aefc6505a3daa3e45e2e111: CPK blob 2ed2cbb2c6112124013ab52755dba8a443e91306; UTF blob d1662d140a48cae37a6696213ee441aed4076edb.
- REA latest checked commit 8ff3570430ad682061b7932b9953d45b904cb487: supported-targets blob b4fad121e917a1a6eb148e72c4ac1daef7d95265; binary-diagnostics blob 76da9004df7abee2831a2b1d9bc32e99d0e03f1c. This is offline AArch64 ELF analysis, not live Switch lifecycle evidence.
- Pinned Switch v1.70 original main Git blob 8af900db0d7003255b4ddb3cbd1289cd5a15458e, 27,701,509 bytes, SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9.

## Prior bounded attempt and first implementation result

The 256-to-1,024 state retry was falsified: on 45 residual pointer-page references it exhausted at 1,024 without resolving any. It is removed in this revision rather than retained as wasted work. Prior raw job log: run 46128778750/job 140929155464. First unknown-bound widening run: 46130420276/job 140934097494, COMPLETED SUCCESS, raw log inspected; artifact ZIP SHA256 f2129afb89b14b9e240f224627ec618c91a6493d38a2df1dfa5f4784b772a1da, report JSON SHA256 d7bdef8c4fbb94f2943ef855ced0b944ea868b1d7e32cb3da265dd32d461967c.

The first widening revision recorded 37 widenings across 27 references and reduced residual state-budget references from 45 to 20. Its disassembly showed multiple real loop shapes: backedges whose first observed state is reached through the backedge itself; update-at-target loops (for example X25 += 1 at 0x1592a0); and nested/multi-counter loops (for example X24 += 8 and X25 += 1 around 0x1642cc).

## Current revision

The CFG stores the first observed abstract state at each PC, including targets first reached through a backedge. It does not claim this state is the loop preheader. On a later in-window backward edge it widens every changed tracked register only if each has an exact self-ADD-immediate chain step, the update lies at or after the backedge target and before the branch, and the observed address delta exactly matches the immediate. Multiple counters are accepted only when every changed common register meets that proof; ambiguous/mixed updates fail closed.

The 1,024-state retry is removed. Residual references retain bounded 64-instruction disassembly. Any reference using unknown-bound widening marks its bounded CFG incomplete and branch witnesses non-exhaustive; pointer alias completeness therefore remains false until the path is proven without widening.

## Regression coverage

- Positive single-counter self-ADD backedge with an unresolved indexed access.
- Positive two-counter self-ADD backedge with both dynamic terms retained.
- Positive preheader branch that skips the update on first entry; the first observed target state is used only as a comparison baseline.
- Negative call-clobbered counter, non-self update, and fail-closed state-budget boundary.
- Authentic pinned-main regression requires at least 27 widened references, at least 37 widened counters, and no more than 20 residual state-budget references; CI fails if these prior results regress.

## Limits

Static host analysis of the exact pinned original main and synthetic CFG tests only. No native consumer ABI, callback identity, object type, ownership/lifecycle, lock/unlock, async, rollback/unbind/destructor, archive precedence, emulated ARM64 execution of this analyzer, Uzuy, or gameplay proof. No game-byte modification or hook. Preserve Sakura aura107 and both Event236 variants. Keep full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false.

## R277H4 follow-up — derived-register provenance and regression repair (2026-11-28)

State at this code revision: PENDING_CI. Parent HEAD: `aab7efd10250aa20ad59eb70fb9aadbb1ec562e4`.

### Research sources rechecked

- NSC-ModManager release/tag `2.1.2.1`: commit `502c38d3ee832509f9ee3951b7d3339826538fec`; `XfbinParser.cs` blob `faf79d588fd8beb3f5761faebedd2252853b2f2b`; `SkillCustomizeParamModel.cs` blob `6a891e237d27fdf01336f806dbef8767d609a304`. Release notes add Switch Projectiles Target only at the PC API layer; parser/model source remains pinned to the same release.
- NSC-Toolbox release/tag `2.1.2.1`: commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; `XfbinParser.cs` blob `86c63708edf2698b5bc1c2a54c0480cce014b525`; `SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`; `Properties/Program.cs` blob `9d5f3e0dfa4ed51cf7924b503081a87b12146f64`.
- UltimateStormAPI 2.1.2.1 commit `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, parent 2.1.2.0 commit `1c3460573fa70b595e6bfa70e52f83f1c3f74f12`, MovesetPlus.cpp blob `d7c5dbbebd60415f8d304321f083897658a86146`. Commands 27/28 existed in the parent; command 29 is newly added. Its code reads PC player offset 0xE60 on 1.70, uses Windows std::mutex/GetTickCount64, a 250 ms active freshness window and 250 ms pending expiry. This is not Switch ABI evidence.
- PyCriCodecs source pin: commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; CPK blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; UTF blob `d1662d140a48cae37a6696213ee441aed4076edb`.
- Independent CPK reference `BogdanLask/cpk-runtime`: current main commit `82488818cd72f65c30328a4df6734708366d1ffe`; format note blob `245e5696156c211025057e64885059bd1a79f3d1`. Its format notes distinguish big-endian CPK/@UTF tables from little-endian CRILAYLA headers, use archive-local numeric IDs, and explicitly mark legacy ITOC and higher UTF versions as synthetic-only. It does not establish this game's archive precedence or engine lifetime.
- REA current main commit `3a42ef68312e736a56381eb17b370e67a489c55e`; binary-diagnostics doc blob `1e6ce267a1f6e46e5ff22901c2ae37a216858f1a`. REA's documented native-binary/offline ELF analysis is a tooling reference only; it is not live Switch tracing or ownership evidence.
- Pinned Switch v1.70 original main: Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes, expected SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.

### Reproducible hypothesis and byte-level regression

A bounded backedge can update a counter with a self-ADD and also recompute a pointer register from that counter (AArch64 `ADD X10, X8, X9`). The counter's stride is statically observed, but the loop bound, preheader value, callback preservation and runtime address remain unverified. The analyzer now emits the derived register's counter dependency, abstract backedge address, dynamic terms and source chain, with explicit `runtime_value_verified=false` and `effective_address_resolved=false`. It does not convert the derived pointer into a concrete runtime address.

The synthetic positive case requires the derived X10 chain to depend on widened X9 and requires the later indexed read to retain `LOOP_INDUCTION_UNKNOWN_BOUND`. A negative case introduces an unrelated newly-defined X11 from X8+X8; that must reject the widening. Existing single-counter, two-counter, preheader-skip, call-barrier, non-self-update and state-budget boundary cases remain in the suite.

### CI failure root cause observed before this patch

Push run `46131207431` / job `140936523895` failed in `synthetic_pointer_page_budget_fail_closed`: the test called `scan_address_pages_cfg()` but asserted for `pointer_page_budget_reference_disassembly`, a field produced only by the higher-level `inspect()` report. The raw log showed `KeyError` at test line 535; the scanner correctly exposes `page_references` and budget state instead. The fix asserts the low-level schema and keeps the full-main disassembly assertion in the authentic `inspect()` regression.

No ABI, callback, object type, ownership/lifecycle, lock/unlock, async, rollback/unbind/destructor, archive precedence, emulated ARM64 analyzer execution, Uzuy or gameplay proof. No runtime hook or game-byte modification. Preserve Sakura aura107 and both Event236 variants; all three release flags remain false.
