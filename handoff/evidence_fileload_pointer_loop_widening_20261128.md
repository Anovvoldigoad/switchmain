# FileLoad pointer-page unknown-bound loop widening

Date: 2026-11-28
Branch: port/full-api-v170
Parent HEAD: 6fbe8d500932387c031a363e55bad20577186da6
State: PENDING_CI

## Primary-source recheck

- NSC-ModManager release 2.1.2.1: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1, tag commit 502c38d3ee832509f9ee3951b7d3339826538fec. The pinned XfbinParser.cs blob is faf79d588fd8beb3f5761faebedd2252853b2f2b; SkillCustomizeParamModel.cs is 6a891e237d27fdf01336f806dbef8767d609a304. The same files fetched at upstream main are byte-identical to the tag.
- NSC-Toolbox release 2.1.2.1: https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1, tag commit 789fe96f99cdaa77f952b90b563c6e3f49b6d697. The pinned parser blob is 86c63708edf2698b5bc1c2a54c0480cce014b525; SkillEditorModel.cs is e165471682e4a7aed91094ef07f92df271f31639. These parser/editor files remain unchanged relative to upstream main.
- UltimateStormAPI 2.1.2.1: https://github.com/TheLeonX/UltimateStormAPI/blob/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc/xinput9_1_0/MovesetPlus.cpp, commit a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc, blob d7c5dbbebd60415f8d304321f083897658a86146. Its new command 29 uses Windows mutex/timing and is not Switch ABI evidence.
- Independent CRI reference: PyCriCodecs commit 755055ee7b056c9c1aefc6505a3daa3e45e2e111; CPK blob 2ed2cbb2c6112124013ab52755dba8a443e91306, UTF blob d1662d140a48cae37a6696213ee441aed4076edb. The separate CPK runtime format note describes big-endian CPK/@UTF framing and little-endian CRILAYLA fields, but explicitly limits what is observed versus synthetic.
- REA commit 76e319b80fe207f05b6558053a8f66264680820d; supported-targets blob b4fad121e917a1a6eb148e72c4ac1daef7d95265, binary-diagnostics blob 76da9004df7abee2831a2b1d9bc32e99d0e03f1c. Its documented offline AArch64 ELF diagnostics run on Linux x64 and do not supply live registers or game lifecycle.
- Pinned Switch v1.70 original main: repository blob 8af900db0d7003255b4ddb3cbd1289cd5a15458e, 27,701,509 bytes, SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. The dedicated CI test re-hashes this exact input.

## Falsified prior retry

The prior 256-to-1,024 state-budget retry was not a useful reduction: all 45 pointer-page references still exhausted at exactly 1,024 states. The previous test required a nonzero resolved count; the raw job log for run 46128778750/job 140929155464 showed that assertion failing. The failed run still uploaded report artifact 15256429366; its report SHA256 is to be recorded after this revision's CI.

## New implementation

The CFG now performs a conservative widening only when an in-window backward edge returns to a previously reached header and exactly one tracked register differs by one observed self-ADD immediate instruction. The analyzer converts that register to an explicit LOOP_INDUCTION_UNKNOWN_BOUND term and re-seeds the same symbolic state at the increment site. It refuses widening when more than one tracked register changes, the changed register was not updated by a self-ADD immediate, the stride does not exactly equal the observed address delta, the update is outside the backedge body, or a call barrier has erased the tracked register state.

The new term is not a concrete address or loop bound. Branch-path witnesses are marked non-exhaustive; call/callback preservation, loop count, and effective address remain unproven. The prior 1,024-state retry remains a bounded second attempt for references not reduced by the widening. Remaining budget-limited pointer references now carry their 64-instruction bounded disassembly in the machine-readable report.

## Regressions

Synthetic positive coverage requires one self-ADD backedge to collapse to one unknown-bound symbolic state while preserving an unresolved indexed memory candidate. Negative cases reject a call-clobbered counter, two simultaneously changed tracked registers, and a non-self update. The authentic original-main test requires at least one previously budget-limited pointer reference to be reduced by the new analysis; otherwise CI fails.

## Scope boundary

Static analysis of the pinned original main plus synthetic host tests only. No native consumer ABI, callback identity, object type, ownership/lifecycle, lock/unlock, async, rollback/unbind/destructor, archive precedence, emulated ARM64 execution of this analyzer, Uzuy, or gameplay proof. No hook or game-byte change. Preserve Sakura aura107 and both Event236 variants. Keep all three release flags false.
