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

State at this code revision: VERIFIED_STATIC_CI_ONLY (code commit 440c808f5c41237ddf72855d2f583d45a446399d; parent aab7efd10250aa20ad59eb70fb9aadbb1ec562e4). Parent HEAD: `aab7efd10250aa20ad59eb70fb9aadbb1ec562e4`.

### Research sources rechecked

- NSC-ModManager release/tag `2.1.2.1`: commit `502c38d3ee832509f9ee3951b7d3339826538fec`; `XfbinParser.cs` blob `faf79d588fd8beb3f5761faebedd2252853b2f2b`; `SkillCustomizeParamModel.cs` blob `6a891e237d27fdf01336f806dbef8767d609a304`. Release notes add Switch Projectiles Target only at the PC API layer; parser/model source remains pinned to the same release.
- NSC-Toolbox release/tag `2.1.2.1`: commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; `XfbinParser.cs` blob `86c63708edf2698b5bc1c2a54c0480cce014b525`; `SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`; `Properties/Program.cs` blob `9d5f3e0dfa4ed51cf7924b503081a87b12146f64`.
- UltimateStormAPI 2.1.2.1 commit `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, parent 2.1.2.0 commit `1c3460573fa70b595e6bfa70e52f83f1c3f74f12`, MovesetPlus.cpp blob `d7c5dbbebd60415f8d304321f083897658a86146`. Commands 27/28 existed in the parent; command 29 is newly added. Its code reads PC player offset 0xE60 on 1.70, uses Windows std::mutex/GetTickCount64, a 250 ms active freshness window and 250 ms pending expiry. This is not Switch ABI evidence.
- PyCriCodecs source pin: commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; CPK blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; UTF blob `d1662d140a48cae37a6696213ee441aed4076edb`.
- Independent CPK reference `BogdanLask/cpk-runtime`: current main commit `82488818cd72f65c30328a4df6734708366d1ffe`; format note blob `245e5696156c211025057e64885059bd1a79f3d1`. Its format notes distinguish big-endian CPK/@UTF tables from little-endian CRILAYLA headers, use archive-local numeric IDs, and explicitly mark legacy ITOC and higher UTF versions as synthetic-only. It does not establish this game's archive precedence or engine lifetime.
- REA current main commit `3a42ef68312e736a56381eb17b370e67a489c55e`; binary-diagnostics doc blob `1e6ce267a1f6e46e5ff22901c2ae37a216858f1a`. REA's documented native-binary/offline ELF analysis is a tooling reference only; it is not live Switch tracing or ownership evidence.
- Pinned Switch v1.70 original main: Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes, expected SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.


### Primary-source byte-layout cross-check and correction

- NSC-ModManager's `BinaryReader.cs` blob `cc49eedef1578b37d381d23f5f09ac2567009149` implements `b_byteArrayToIntRev` with `BinaryPrimitives.ReadInt32BigEndian`. Its 2.1.2.1 `XfbinParser.cs` uses a 0x44-byte header; NUCC count/size at 0x1C/0x20; path count at 0x24 with a minus-one adjustment; path size at 0x28; name count/size at 0x2C/0x30; Bin1 size at 0x38; and animation-section size at 0x40. Toolbox 2.1.2.1 shares the same parser blob family but adds a Bin2-size field at 0x3C multiplied by four and a first-chunk-index calculation. These are PC XFBIN parser/editor layouts, not engine consumer ABI.
- PyCriCodecs `chunk.py` blob `aab0cf82b7ce599811762bda3a089cb0f8aa41b4` defines CPK packet header `<4sIII` (little-endian fields) and UTF header `>4sIIIIIHHI` (big-endian fields). Its CPK TOC extraction path uses a fixed `0x800 + FileOffset`; the independent cpk-runtime format note instead documents the TOC base as `min(TOC packet offset, ContentOffset)` for observed layouts. Do not promote the PyCriCodecs 0x800 convention to a universal CPK rule. PyCriCodecs also decodes EUTF with the 0x655f/0x4115 LCG and handles ITOC from ContentOffset.
- Correction to older REA assumptions: current REA commit `3a42ef68312e736a56381eb17b370e67a489c55e` binary-diagnostics blob `1e6ce267a1f6e46e5ff22901c2ae37a216858f1a` explicitly says initial real verification covers Linux x64 ELF64 x86-64. It is not an AArch64 decoder or Switch runtime tracer. The repo's Capstone-based AArch64 work remains its own pinned static analysis path; do not cite REA as proof of AArch64 support.

### Reproducible hypothesis and byte-level regression

A bounded backedge can update a counter with a self-ADD and also recompute a pointer register from that counter (AArch64 `ADD X10, X8, X9`). The counter's stride is statically observed, but the loop bound, preheader value, callback preservation and runtime address remain unverified. The analyzer now emits the derived register's counter dependency, abstract backedge address, dynamic terms and source chain, with explicit `runtime_value_verified=false` and `effective_address_resolved=false`. It does not convert the derived pointer into a concrete runtime address.

The synthetic positive case requires the derived X10 chain to depend on widened X9 and requires the later indexed read to retain `LOOP_INDUCTION_UNKNOWN_BOUND`. A negative case introduces an unrelated newly-defined X11 from X8+X8; that must reject the widening. Existing single-counter, two-counter, preheader-skip, call-barrier, non-self-update and state-budget boundary cases remain in the suite.

### CI failure root cause observed before this patch

Push run `46131207431` / job `140936523895` failed in `synthetic_pointer_page_budget_fail_closed`: the test called `scan_address_pages_cfg()` but asserted for `pointer_page_budget_reference_disassembly`, a field produced only by the higher-level `inspect()` report. The raw log showed `KeyError` at test line 535; the scanner correctly exposes `page_references` and budget state instead. The fix asserts the low-level schema and keeps the full-main disassembly assertion in the authentic `inspect()` regression.

No ABI, callback, object type, ownership/lifecycle, lock/unlock, async, rollback/unbind/destructor, archive precedence, emulated ARM64 analyzer execution, Uzuy or gameplay proof. No runtime hook or game-byte modification. Preserve Sakura aura107 and both Event236 variants; all three release flags remain false.

### Verified Actions on the R277H5 code commit

- Targeted FileLoad workflow run `46135363784`, job `140949354184`: COMPLETED SUCCESS; raw job log inspected; marker `PINNED_FILELOAD_TABLE_CFG_PASS`. Artifact `15259811643`, ZIP SHA256 `db171ec74c60f898bdc4489c2925a0bbf93e904842c2e36d079d937de98f9810`; report JSON SHA256 `13528ae1baeca899cf0d5debd5a947ea7abca045525310e1d4e47bf78a0bb970`; source SHA256SUMS file SHA256 `bdf2b896e3fc21f4a9fc1077150d1edcc1820f4531034932687fe9c79c45dffe`.
- Broad foundation run `46135363770`, job `140949354174`: COMPLETED SUCCESS; all 97 job steps completed; raw log inspected; 74 JSON proof files; artifact `15258974881`, ZIP SHA256 `db9c10abfed9af1e0b7873e8b2c8a6b5621c60b8fd82c76e76e51bbacc1bb460`; release-flag marker `RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS 26 NO_UZUY_PROOF`.
- Authentic report counts: 61,914 candidate ADRP references; 4,055 traced under the 4,096 cap; 8 pages skipped; zero state-budget-exhausted references; 45 references with 63 unknown-bound loop widenings; target-page CFG complete, pointer-alias trace incomplete. There are 34 direct accesses, 9 indexed candidates, 32 branch-path write rows, 214 static pointer cells, 271 loaded aliases and 1 ambiguous load. The authentic report contains zero derived-register evidence rows; the positive/negative derived-register behavior is proven only by synthetic fixtures.
- The earlier run `46131207431` / job `140936523895` failed before authentic-main analysis because the synthetic budget test asserted an inspect()-only key on the low-level scanner. R277H5 fixes that test contract; the successful targeted run now reaches the authentic SHA check and report generation.

No ABI, object type, callback, ownership/lifecycle, lock/unlock, async, rollback/unbind/destructor, archive precedence, emulated ARM64 execution of this analyzer, Uzuy or gameplay proof. The broad foundation's separate modeled/emulated slices do not promote this FileLoad analyzer to runtime status. No game-byte modification or hook. Preserve Sakura aura107 and both Event236 variants; all three release flags remain false.

