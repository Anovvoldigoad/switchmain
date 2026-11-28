# FileLoad pointer-page CFG bounded retry

Date: 2026-11-28
Branch: `port/full-api-v170`
Parent HEAD: `a8788fc501040e840fc3e163438d0c63f93ac75e`
State: PENDING_CI

## Research-first primary sources rechecked

- [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`. `XfbinParser.cs` blob `faf79d588fd8beb3f5761faebedd2252853b2f2b` and `SkillCustomizeParamModel.cs` blob `6a891e237d27fdf01336f806dbef8767d609a304` were fetched again at both the tag and current `main`; each pair is byte-identical.
- [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1), tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`. `XfbinParser.cs` blob `86c63708edf2698b5bc1c2a54c0480cce014b525`, `SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`, and `SkillCustomizeParamModel.cs` blob `1b45c89ca9d36b6db874603cdc28290d2b019f25` were fetched at tag and current `main`; all are byte-identical.
- [UltimateStormAPI MovesetPlus.cpp](https://github.com/TheLeonX/UltimateStormAPI/blob/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc/xinput9_1_0/MovesetPlus.cpp), commit `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, blob `d7c5dbbebd60415f8d304321f083897658a86146`; parent `1c3460573fa70b595e6bfa70e52f83f1c3f74f12`, blob `e96af51210e96926a7bdaa70c44b6645f1a2b2b6`. Case 29 is the new PC Windows projectile-takeover command; it uses `std::mutex`, `GetTickCount64`, and 250 ms windows. It is not a Switch ABI.
- [PyCriCodecs CPK](https://github.com/t-wy/PyCriCodecs/blob/755055ee7b056c9c1aefc6505a3daa3e45e2e111/PyCriCodecs/cpk.py), commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`, blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; [UTF](https://github.com/t-wy/PyCriCodecs/blob/755055ee7b056c9c1aefc6505a3daa3e45e2e111/PyCriCodecs/utf.py), blob `d1662d140a48cae37a6696213ee441aed4076edb`. These are independent CRI CPK/@UTF layout references only.
- [REA supported targets](https://github.com/morluto/rea/blob/76e319b80fe207f05b6558053a8f66264680820d/docs/reference/supported-targets.md), commit `76e319b80fe207f05b6558053a8f66264680820d`, blob `b4fad121e917a1a6eb148e72c4ac1daef7d95265`; [binary diagnostics](https://github.com/morluto/rea/blob/76e319b80fe207f05b6558053a8f66264680820d/docs/guides/native/binary-diagnostics.md), blob `76da9004df7abee2831a2b1d9bc32e99d0e03f1c`. REA documents offline ELF64 little-endian AArch64 inspection with caller-supplied pwntools on Linux x64; it is not live register or engine lifecycle evidence.
- Pinned Switch v1.70 original main: repository blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes, SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`. Existing FileLoad CI rehashed this exact byte fixture.

## Baseline byte evidence

The prior targeted FileLoad report is artifact `15255315717`, report SHA256 `19e379f8e8595d1138fe7db417e28e2c4e320147a811116fe8302e93af1c19ba`. It records 4,055 ADRP references, 3,966 pointer-page references, and 45 pointer-page references that reached the 256-state cap. Those 45 references are distributed over three pages: `0x2145000` (17), `0x2148000` (7), and `0x214c000` (21). Each exhausted reference had exactly 256 reachable states and only 15–63 decoded instruction addresses, with no undecodable words. This is consistent with multiple abstract register states at a small set of instruction addresses; it is not proof of a function or object identity.

## Implementation and falsifiable hypothesis

- The analyzer now retries only non-target pointer-page references that hit the original 256-state budget, once, with a hard cap of 1,024 states.
- The target table page is never retried or widened by this policy. Calls remain clobber barriers; out-of-window edges remain un-followed; no BSS/heap runtime pointer values are inferred.
- The first attempt is discarded when retry runs; only the retry's state/access evidence is aggregated, preventing duplicate rows.
- Every reference records the initial/retry budgets, reachable-state counts, and whether the retry resolved the budget. Aggregate counters report attempted/resolved/unresolved pointer-page retries.
- Synthetic regressions cover a pointer-page CFG that is incomplete at one state and complete at 1,024, target-page non-retry, and no-retry boundary. The authentic-main regression requires at least one of the 45 previously exhausted pointer-page references to resolve; if not, CI fails rather than claiming progress.

Expected falsifier: if none of the 45 pointer-page references resolves at 1,024 states, the implementation is not a useful blocker reduction and must be revised or reverted. A retry that remains budget-limited stays explicitly unresolved.

## CI

Pending on the new code commit. The workflow is the existing SHA-pinned FileLoad registration lifecycle workflow and will execute the original-main SHA guard, synthetic regressions, 4,055-reference scan, and artifact generation.

## Scope boundary

Static original-main analysis plus synthetic host tests only. No consumer ABI, object ownership, callback, lock/unlock, async completion, rollback/unbind/destructor, archive precedence, emulated ARM64, Uzuy, or gameplay proof. No runtime hook. Preserve Sakura aura107 and Event236 marker `0x4E53` + `0x2A` plus the no-marker variant. Keep all three release flags false.
