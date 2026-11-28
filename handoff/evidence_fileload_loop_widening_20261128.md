# FileLoad counted-loop induction widening

Date: 2026-11-28  
Branch: `port/full-api-v170`  
Parent HEAD: `c0649a2c899eb74c69bb0df177c232e413cc9846`  
State: VERIFIED_STATIC_CI_ONLY

Code commit: `2101530170402945bfa4165b1c01e06d944c2e48` (parent `c0649a2c899eb74c69bb0df177c232e413cc9846`)

## Research-first primary sources rechecked

| Source | Exact ref | Verified source identity / relevance |
|---|---|---|
| [NSC-ModManager release 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | Tag `502c38d3ee832509f9ee3951b7d3339826538fec`; main `276116ebf5ba398a867793cb02ee6c33c0927645) | `XfbinParser.cs` blob `faf79d588fd8beb3f5761faebedd2252853b2f2b`; `SkillCustomizeParamModel.cs` blob `6a891e237d27fdf01336f806dbef8767d609a304`. Tag and main are parent/child; relevant parser/model blobs are identical. |
| [NSC-Toolbox release 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | Tag `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; main `6f780cb6814f07e03c16b3e78d97dde4e4368983) | `XfbinParser.cs` blob `86c63708edf2698b5bc1c2a54c0480cce014b525`; `SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`. Relevant parser/editor blobs match the release tag. |
| [UltimateStormAPI 2.1.2.1](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | Commit `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, parent `1c3460573fa70b595e6bfa70e52f83f1c3f74f12) | `MovesetPlus.cpp` blob `d7c5dbbebd60415f8d304321f083897658a86146` adds case 29 `TakeOverEnemyProjectiles`; the method uses Windows mutex/tick APIs and PC projectile state. This is not a Switch ABI or safe transplant. |
| [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | main `755055ee7b056c9c1aefc6505a3daa3e45e2e111` | `PyCriCodecs/cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; `utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`. Independent CPK/TOC/ITOC/@UTF format reference only. |
| [REA](https://github.com/morluto/rea/tree/76e319b80fe207f05b6558053a8f66264680820d) | latest main `76e319b80fe207f05b6558053a8f66264680820d` | `docs/reference/supported-targets.md` blob `b4fad121e917a1a6eb148e72c4ac1daef7d95265`; `docs/guides/native/binary-diagnostics.md` blob `76da9004df7abee2831a2b1d9bc32e99d0e03f1c`. REA documents offline ELF64 little-endian AArch64 layout using caller-supplied pwntools 4.15.0 on Linux x64 and built-in Switch NSO/NRO header parsing; it does not provide live register capture or consumer lifecycle proof. |
| Pinned Switch v1.70 original main | Repository blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes | Required SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`. Previous targeted CI on parent HEAD rehashed this exact file and emitted the raw static report. |

## Baseline evidence and byte layout

The preceding targeted run on HEAD `c0649a2c899eb74c69bb0df177c232e413cc9846` was run `46122662118`, job `140910332424`, artifact `15254183663`. Its raw log contained `PINNED_FILELOAD_TABLE_CFG_PASS`. Artifact ZIP SHA256: `efeccb5ead49ba200e26cba0388bae86810102c78f82e7c7622b500a9a62f50e`; extracted report JSON SHA256: `7733c3d01170e81dc36573024496ac985c57b14a98946170f7480b5d8c7e8c46`.

That report found 4,055 ADRP references: 89 to target page `0x4371000` and 3,966 to candidate pointer pages. It had 47 state-budget references (2 target-page, 45 pointer-page), 214 static pointer cells, 271 unique loaded aliases, and one ambiguous pointer load. The 64-slot table is BSS `[0x4371800, 0x4371a00)`, 64 entries × 8 bytes.

Two exact target-page loop candidates:

| ADRP site | Loop bytes SHA256 | Counter | Dispatch slot offset |
|---|---|---|---|
| `0x116bf54` | `df7bdfbe579db712c6cb51a69ca69105acf2140a655759f462c2a6e896caa91b` | X20 = 0; +8; compare 0x200 | 0x60 |
| `0x116bfac` | `708f2801f32244ed5149582077bf1e4cc09c5a989c102dffd4b3445082a7b16e` | X20 = 0; +8; compare 0x200 | 0x68 |

Both have caller-side table address expression `0x4371800 + X20`: X21 is formed from ADRP page `0x4371000` plus `0x7d8`, then X8 = X21 + X20, then an eight-byte `LDR X0,[X8,#0x28]`. A non-null entry follows `LDR X8,[X0]`, then loads the indirect target at `[X8,#0x60]` or `[X8,#0x68]`, and executes `BLR X8`; the return accumulator is X19.

## Implementation

- Source: `tools/portlib/native_fileload_table_cfg.py`, new blob `4fb38a1c477723b7ad0f59921d68613adbb38be1`.
- Regression/driver: `tests/test_native_fileload_table_cfg.py`, new blob `9cf962a0bec50eae6af10e079d01ae0ee60e0c2b`.
- The scanner recognizes only the exact pinned 64-slot loop instruction sequence and canonicalizes X20 as a symbolic `LOOP_INDUCTION` term (initial 0, stride 8, bound 0x200) while the caller-side register state remains known.
- This exposes the two eight-byte indexed table reads at `0x116bf70` and `0x116bfc8` with base `0x4371800`, dynamic index X20, stride 8 and bound 0x200, without enumerating every loop iteration.
- Crucially, every BLR remains a clobber barrier. If control returns from the indirect call, tracked X20 is not reintroduced unless it was still present in the incoming abstract state. The analyzer does not assume the callback preserves X20.
- Synthetic positive, malformed-stride negative, call-barrier and table-range tests were added. The authentic-main driver still checks the pinned SHA and prior linear witnesses.

## Falsifiable hypothesis

The exact-loop induction abstraction should remove the two target-page state-budget failures and expose the two loop reads as symbolic indexed reads. If the loop bytes, counter init/stride/bound, dispatch offset, or caller-side register provenance differs, widening must not apply. The 45 pointer-page budget references remain independent and must not be hidden.

## CI

Targeted FileLoad workflow run [46124030962](https://github.com/Anovvoldigoad/switchmain/actions/runs/46124030962) / job `140914501509`: COMPLETED SUCCESS; raw job log inspected. Marker: `PINNED_FILELOAD_TABLE_CFG_PASS adrp_refs 4055 direct_accesses 34 indexed_accesses 9 branch_path_writes 32 static_pointer_cells 214 loaded_aliases 271 NO_ABI_NO_OWNER_NO_ARCHIVE_PRECEDENCE_NO_UZUY_CLAIM`. Artifact `15255315717`, ZIP SHA256 `f8a95dc28b93472956194ddc457326616cdb971252191841e5ddd9a743c12cc9`; report JSON SHA256 `19e379f8e8595d1138fe7db417e28e2c4e320147a811116fe8302e93af1c19ba` (6,454,239 bytes). The authentic main hash passed. Target-page state-budget references fell 2→0; global state-budget references fell 47→45; target-page bounded CFG is complete, but pointer-page alias tracing and whole-window completeness remain false. Two new symbolic indexed reads were exposed at `0x116bf70` and `0x116bfc8`.

Release-flag guard run [46124031110](https://github.com/Anovvoldigoad/switchmain/actions/runs/46124031110) / job `140914502015`: COMPLETED SUCCESS; raw log inspected; marker `RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS 26 NO_UZUY_PROOF`. The broad foundation workflow run `46124031004` / job `140914502057` was still IN_PROGRESS at checkpoint finalization and is tracked separately.

## Scope boundary

This is host-side static analysis of original pinned bytes plus synthetic AArch64 fixtures. It is not runtime register capture, callback identity, object type, native consumer ABI, ownership/lifecycle, lock/unlock, async completion, rollback/unbind/destructor, archive precedence, emulated ARM64, Uzuy or gameplay proof. No hook is installed. Sakura aura107 and both Event236 marker variants remain untouched. `full_moddingapi=false`, `ready_for_gameplay_test=false`, and `emulator_tested=false` remain unchanged.
