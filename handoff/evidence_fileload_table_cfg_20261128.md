# FileLoad bounded CFG + static pointer-alias census

Date: 2026-11-28  
Branch: \`port/full-api-v170\`  
Parent HEAD: \`4d5acd5a52e0ae3e72415a7ee3164ffc21082769\`  
State at code commit: PENDING_CI

## Research-first primary sources rechecked

| Primary source | Exact current ref | Retrieved source identity and verified delta |
|---|---|---|
| [NSC-ModManager release 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag \`502c38d3ee832509f9ee3951b7d3339826538fec\`, published 2026-08-30; latest main \`276116ebf5ba398a867793cb02ee6c33c0927645\` | \`XfbinParser.cs\` blob \`faf79d588fd8beb3f5761faebedd2252853b2f2b\`; \`Model/SkillCustomizeParamModel.cs\` \`6a891e237d27fdf01336f806dbef8767d609a304\`; \`Model/SpSkillCustomizeParamModel.cs\` \`2b518f6eeb9ef97895517582e393a2adf9ee6da0\`. Tag and pinned-main parser/model blob IDs match. Release adds Switch Projectiles Target. |
| [NSC-Toolbox release 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | tag \`789fe96f99cdaa77f952b90b563c6e3f49b6d697\`, published 2026-08-30; latest main \`6f780cb6814f07e03c16b3e78d97dde4e4368983\` | \`XfbinParser.cs\` blob \`86c63708edf2698b5bc1c2a54c0480cce014b525\`; \`Model/SkillEditorModel.cs\` \`e165471682e4a7aed91094ef07f92df271f31639\`. Tag and pinned-main parser/editor blob IDs match. |
| [UltimateStormAPI](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | pin \`a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc\`, parent \`1c3460573fa70b595e6bfa70e52f83f1c3f74f12\` | \`MovesetPlus.cpp\` latest blob \`d7c5dbbebd60415f8d304321f083897658a86146\`, parent blob \`e96af51210e96926a7bdaa70c44b6645f1a2b2b6\`. Cases 27/28 and deflection already exist in the parent; case 29 \`TakeOverEnemyProjectiles\` is new and uses \`std::mutex\` / \`GetTickCount64\` on PC Windows. No Switch ABI inference. |
| [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | latest main \`755055ee7b056c9c1aefc6505a3daa3e45e2e111\` | \`PyCriCodecs/cpk.py\` blob \`2ed2cbb2c6112124013ab52755dba8a443e91306\`; \`utf.py\` \`d1662d140a48cae37a6696213ee441aed4076edb\`. CPK/TOC/ITOC/@UTF format parsing and extraction reference only; no Switch archive winner/async semantics. |
| [REA](https://github.com/morluto/rea/tree/8ff3570430ad682061b7932b9953d45b904cb487) | latest main \`8ff3570430ad682061b7932b9953d45b904cb487\` | README blob \`d6f1a30cb05a07fbfd1d923f44f7ca569e000b1b\`; native binary diagnostics guide \`76da9004df7abee2831a2b1d9bc32e99d0e03f1c\`; supported-targets guide \`b4fad121e917a1a6eb148e72c4ac1daef7d95265\`. Current REA supports ELF64 little-endian AArch64 offline layout with caller-supplied pwntools 4.15.0 on Linux x64, plus Switch NSO/NRO header parsing. These are static tools, not runtime register capture or consumer lifecycle evidence. |
| Pinned Switch v1.70 original main | repo blob \`8af900db0d7003255b4ddb3cbd1289cd5a15458e\`, 27,701,509 bytes | Required SHA256 \`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9\`. The new CI test rehashes this exact tracked file before analysis. |

## Why this slice

The preceding verified static scan found 89 ADRP references to page \`0x4371000\`, seven UXTW-indexed reads, 34 direct accesses and no indexed writers in bounded linear windows. It did not follow conditional/unconditional branch paths or file-backed pointer loads. This change adds those two bounded dimensions without weakening any unknown/call barrier.

## Implementation

- New analyzer: \`tools/portlib/native_fileload_table_cfg.py\`.
- New regression/driver: \`tests/test_native_fileload_table_cfg.py\`.
- Starts from each aligned ADRP reference to the target page and any page containing a static pointer cell into the target page.
- Follows only in-window AArch64 conditional/unconditional edges. Calls (including authenticated indirect calls) are opaque clobber barriers; branch targets outside the 0x100-byte window are recorded, not followed.
- Pointer aliases are accepted only from aligned file-backed 64-bit literals or symbol-zero \`R_AARCH64_RELATIVE\` addends. A loaded pointer must resolve uniquely into the target 4 KiB page before it is propagated. BSS/heap values without relocations remain unknown.
- The analyzer cross-checks that all prior linear witnesses remain present.
- Synthetic tests cover branch-only stores, out-of-window targets, call-clobber barriers, literal/RELA pointer cells, BSS exclusion, ambiguous aliases, target-page-end boundary, and state-budget exhaustion.
- Original main SHA256 remains pinned; no game bytes are modified.

## Falsifiable hypothesis

If a producer writes the 64-slot table through an in-window conditional branch or a file-backed/RELA-backed pointer alias, the report must expose the exact instruction word, access direction, effective/static base expression, source cell and branch witness. If no such witness appears, the negative result applies only to scanned ADRP pages, file-backed pointer cells, single-level static loads and bounded CFG windows; dynamic BSS/heap aliases and paths beyond calls/window exits remain unresolved.

## CI

Awaiting the targeted push workflow on the exact code commit. Do not promote this evidence to verified until the job is COMPLETED SUCCESS and the raw log is inspected.

## Scope boundary

This remains host-side static analysis of the exact original main plus synthetic fixtures. It is not ARM64 emulation, a runtime snapshot, a complete writer census, function identity, native consumer ABI, callback identity, object type, ownership/lifecycle, lock/unlock, async completion, rollback/unbind/destructor, archive precedence, Uzuy or gameplay proof. No runtime hook is installed. Sakura aura107 and both Event236 marker variants are untouched; \`full_moddingapi=false\`, \`ready_for_gameplay_test=false\`, and \`emulator_tested=false\` remain unchanged.
