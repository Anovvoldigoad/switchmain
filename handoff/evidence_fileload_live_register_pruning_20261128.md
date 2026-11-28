# FileLoad bounded-CFG live-register pruning

Date: 2026-11-28
Branch: `port/full-api-v170`
Parent HEAD: `ffc586ae6eec952e52bd9e9161ab82facbf97873`
State: PENDING_CI

## Research-first primary sources and exact identities

| Source | Exact ref checked this execution | Relevant blob / observation |
|---|---|---|
| [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | release published 2026-08-30; tag `502c38d3ee832509f9ee3951b7d3339826538fec`; main `276116ebf5ba398a867793cb02ee6c33c0927645` | `XfbinParser.cs` blob `faf79d588fd8beb3f5761faebedd2252853b2f2b` is identical at tag and main. The parser declares a 0x44-byte header and reads the listed section integers in reversed byte order (big-endian). This is PC tooling, not Switch consumer ABI. |
| [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | release published 2026-08-30; tag `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; main `6f780cb6814f07e03c16b3e78d97dde4e4368983` | `XfbinParser.cs` blob `86c63708edf2698b5bc1c2a54c0480cce014b525` is identical at tag and main. Header/section layout matches the ModManager parser. |
| [UltimateStormAPI](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | current main `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`; parent `1c3460573fa70b595e6bfa70e52f83f1c3f74f12` | `MovesetPlus.cpp` blob `d7c5dbbebd60415f8d304321f083897658a86146`. PC command 29 `TakeOverEnemyProjectiles` is new versus parent; commands 27/28 already existed. The 1.70 code uses PC player offset 0xE60, `std::mutex`, `GetTickCount64`, and PC projectile state. No Switch ABI inference or hook. |
| [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | main commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111` | `cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; `chunk.py` blob `aab0cf82b7ce599811762bda3a089cb0f8aa41b4`. Its TOC reader uses fixed 0x800 + FileOffset. |
| [cpk-runtime](https://github.com/BogdanLask/cpk-runtime/tree/82488818cd72f65c30328a4df6734708366d1ffe) | main commit `82488818cd72f65c30328a4df6734708366d1ffe` | `docs/format.md` blob `245e5696156c211025057e64885059bd1a79f3d1` describes BE CPK/@UTF fields and TOC base `min(TOC packet offset, ContentOffset)`. This conflicts with PyCriCodecs' fixed 0x800 base; neither is treated as a universal Storm rule. |
| [REA](https://github.com/morluto/rea/tree/0c7ebd68c4818a55cdd013ac73ccd9b41e141e07) | current main `0c7ebd68c4818a55cdd013ac73ccd9b41e141e07` | `binary-diagnostics.md` blob `76da9004df7abee2831a2b1d9bc32e99d0e03f1c`. It documents Linux x64 host verification, with AArch64 as a target object profile; Linux arm64 host capability is unavailable. It is offline diagnostics, not live Switch execution or lifecycle proof. |
| Pinned Switch v1.70 original main | repository blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes | SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`. The parent branch CI rehashed this file via the SHA-guarded test at run `46138481303` / job `140958974223`; this change revalidates it again. |

## Baseline and falsifiable hypothesis

The previous verified report from code commit `31dceba3697d2a50c41ad8c9ada9b24027230696` found 61,914 ADRP candidates, traced 21,386 across 29 pages, and left 17 per-reference state-budget exhaustions at 256 states each. It also recorded 366 references with 510 unknown-bound loop widenings, 40,528 omitted ADRP candidates from two sampled pages, and 1,617 same-page loaded aliases with zero values inside exact table range `[0x4371800,0x4371A00)`. None of those aliases is a proven table pointer.

The old state key included every tracked address register and its full provenance chain even when that register is overwritten before any use in the bounded window. The new bounded backward-liveness pass computes the union of conditional successors, treats direct/indirect calls as kill barriers (matching the tracer's reset of all tracked state at every call), and treats an undecodable in-window successor as keeping every tracked address register live. The state key now includes exact value/terms/provenance only for registers live at that PC. Dead-register merges are counted separately; live register provenance is never dropped. Loop-induction backedge analysis still receives the full representative register map; liveness pruning applies only to CFG state identity. The per-reference cap remains 256; this is not a budget increase.

Falsifiable tests:
- Positive: two branch paths set X9 to different ADRP pages, but X9 is never read before the bounded window ends; at the join they should merge and stay within a eight-state budget while preserving the X8 table write.
- Negative: two paths set X9 to different values and the join consumes X9 in `ADD X10,X8,X9`; both distinct table writes must remain.
- Boundary: a conditional successor that consumes X9 keeps X9 live at the branch; a BLR target register remains live at the call, but a register used only after the call is not live across the call barrier.

## Scope boundary

This is host-side static analysis of the exact pinned Switch main plus synthetic CFG regressions. It does not identify the FileLoad producer, resolve `[X8,#0x58] -> BR X2` at `0x116b3d0`, prove the native consumer ABI, callback identity, ownership/lifetime, lock/unlock, async completion, rollback/unbind/destructor, or archive precedence. No runtime hook or game-byte edit is authorized. Sakura aura107 and both Event236 variants remain untouched; all three gameplay release flags remain false.
