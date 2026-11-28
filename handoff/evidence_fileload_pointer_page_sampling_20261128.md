# FileLoad pointer-page bounded sampling

Date: 2026-11-28
Branch: `port/full-api-v170`
Parent HEAD: `9e2068a3a9c32ab91e1ed37f01bdb27f31768327`
State: PENDING_CI

## Research-first primary sources

| Source | Exact current ref | Relevant source identity |
|---|---|---|
| [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | release 379313827; main commit `276116ebf5ba398a867793cb02ee6c33c0927645`; release tag commit `502c38d3ee832509f9ee3951b7d3339826538fec` | `XfbinParser.cs` blob `faf79d588fd8beb3f5761faebedd2252853b2f2b`; `BinaryReader.cs` blob `cc49eedef1578b37d381d23f5f09ac2567009149`. Latest release adds PC Switch Projectiles Target. |
| [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | release 379314127; main commit `6f780cb6814f07e03c16b3e78d97dde4e4368983`; release tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697` | `XfbinParser.cs` blob `86c63708edf2698b5bc1c2a54c0480cce014b525`; `SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`; `Program.cs` blob `9d5f3e0dfa4ed51cf7924b503081a87b12146f64`. Latest release also adds PC Switch Projectiles Target. |
| [UltimateStormAPI 2.1.2.1](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | commit `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, parent `1c3460573fa70b595e6bfa70e52f83f1c3f74f12` | `MovesetPlus.cpp` blob `d7c5dbbebd60415f8d304321f083897658a86146`. Commands 27/28 call SetProjectileDeflection; command 29 calls TakeOverEnemyProjectiles. The implementation reads the PC player-side field at 1.70 offset 0xE60, uses GetTickCount64, std::mutex, and PC-side projectile maps with 250 ms freshness/expiry. This is Windows PC state and ABI, not Switch ABI; no port/hook is justified. |
| [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111` | `cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; `utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`; `chunk.py` blob `aab0cf82b7ce599811762bda3a089cb0f8aa41b4`. Format reference only. |
| [cpk-runtime](https://github.com/BogdanLask/cpk-runtime/tree/82488818cd72f65c30328a4df6734708366d1ffe) | main commit `82488818cd72f65c30328a4df6734708366d1ffe` | `docs/format.md` blob `245e5696156c211025057e64885059bd1a79f3d1`; documents BE CPK/@UTF fields, LE CRILAYLA headers, archive-local numeric IDs, and TOC base min(TOC packet offset, ContentOffset) for observed layouts. It does not establish Storm archive precedence. |
| [REA](https://github.com/morluto/rea/tree/c22c1ab1795677b7a52a840d30257cb1cad28ee7) | main commit `c22c1ab1795677b7a52a840d30257cb1cad28ee7` | supported-targets blob `b4fad121e917a1a6eb148e72c4ac1daef7d95265`; binary-diagnostics blob `76da9004df7abee2831a2b1d9bc32e99d0e03f1c`. Its offline ELF profile is caller-supplied pwntools on Linux x64; AArch64 is a target object profile but Linux arm64 host is explicitly unsupported. It is not live Switch register/lifecycle evidence. |
| Pinned Switch v1.70 original main | repository blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes | Expected SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`; prior exact-main CI run 46135363784 rehashed it successfully. |

## Baseline and bounded hypothesis

The previous verified run 46135363784/job 140949354184 emitted report JSON SHA256 `13528ae1baeca899cf0d5debd5a947ea7abca045525310e1d4e47bf78a0bb970` (artifact ZIP SHA256 `db171ec74c60f898bdc4489c2925a0bbf93e904842c2e36d079d937de98f9810`). Its exact pinned-main report found 61,914 ADRP candidates but traced only 4,055 under a global 4,096-reference cap. Eight pointer pages were skipped:

| Pointer page | Candidate ADRP refs |
|---|---:|
| 0x2143000 | 44,208 |
| 0x2144000 | 4,512 |
| 0x2149000 | 1,461 |
| 0x214d000 | 1,250 |
| 0x214e000 | 1,260 |
| 0x2159000 | 2,120 |
| 0x215c000 | 1,708 |
| 0x215d000 | 1,340 |

The first two pages exceed a 4,096 per-page limit; the other six fit. A blind global increase would trace all 61,914 references and create an unnecessarily large CFG workload. The bounded hypothesis is that a deterministic evenly spaced sample of at most 4,096 ADRP sites per page will add broad address coverage while keeping the total trace cap at 32,768. Sampled pages must remain explicitly non-exhaustive and must never make pointer_alias_trace_complete true.

## Implementation and falsifiable regressions

- Source: `tools/portlib/native_fileload_table_cfg.py`.
- Test: `tests/test_native_fileload_table_cfg.py`.
- Global trace cap: 32,768; per-page cap: 4,096.
- For a pointer page exceeding its cap, select exactly K sites from N sorted ADRP candidates using `floor(i*(N-1)/(K-1))`; the K=1 boundary selects the center candidate. The selected (PC, ADRP destination register) sequence is SHA256-recorded. This preserves deterministic first-to-last coverage without implying completeness.
- The target FileLoad table page is never sampled: if its candidate set exceeds a hard budget, the analyzer fails closed.
- Reports record all per-page candidate counts, sampled-page counts, selected/omitted counts and selected-site hashes. Any sampled or skipped page forces pointer alias trace and branch witness exhaustiveness false.
- Synthetic tests cover deterministic repeatability, multiple pages, exact per-page cap, partial-page sampling, total-budget exhaustion, and invalid zero per-page budget. The authentic pinned-main test asserts the eight formerly skipped pages are all visited or sampled, with exact expected 61,914/21,386 candidate/traced counts and two sampled pages.
- No consumer ABI, ownership, callback, async, rollback/unbind/destructor or archive precedence is inferred.

## CI

Pending for the code commit on this branch. Do not mark this slice verified until the targeted and broad workflow logs are inspected.

## Scope boundary

This is host-side static analysis of pinned original main plus synthetic CFG tests. It is not emulated ARM64 execution of this analyzer, Uzuy, gameplay, or runtime tracing. No game bytes or runtime hooks are changed. Preserve Sakura aura107 and Event236 marker 0x4E53 +0x2A plus the no-marker variant. Keep `full_moddingapi=false`, `ready_for_gameplay_test=false`, and `emulator_tested=false`.
