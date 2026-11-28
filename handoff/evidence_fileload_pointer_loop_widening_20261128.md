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
