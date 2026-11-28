# FileLoad CFG equivalent-state deduplication

Date: 2026-11-28
Branch: `port/full-api-v170`
Parent HEAD: `d1d6a77b0ae1c006b6313534a4206a2e9b055c6d`
State at implementation commit: VERIFIED_STATIC_CI_ONLY

## Research-first source gate

The exact latest release tags and current source heads were re-read through GitHub:
- NSC-ModManager release 2.1.2.1 tag `502c38d3ee832509f9ee3951b7d3339826538fec`; current main `276116ebf5ba398a867793cb02ee6c33c0927645`. Parser blob `faf79d588fd8beb3f5761faebedd2252853b2f2b`; skill model blob `6a891e237d27fdf01336f806dbef8767d609a304`.
- NSC-Toolbox release 2.1.2.1 tag `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; current main `6f780cb6814f07e03c16b3e78d97dde4e4368983`. Parser blob `86c63708edf2698b5bc1c2a54c0480cce014b525`; editor model blob `e165471682e4a7aed91094ef07f92df271f31639`.
- UltimateStormAPI current source `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, parent `1c3460573fa70b595e6bfa70e52f83f1c3f74f12`; MovesetPlus.cpp blobs `d7c5dbbebd60415f8d304321f083897658a86146` and `e96af51210e96926a7bdaa70c44b6645f1a2b2b6`. Current PC source adds command 29 `TakeOverEnemyProjectiles`; it uses Windows mutexes, `GetTickCount64`, and PC engine projectile state. Cases 27/28 already existed in the parent. This is not Switch ARM64 ABI evidence.
- PyCriCodecs current main `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; CPK blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; UTF blob `d1662d140a48cae37a6696213ee441aed4076edb`. Its CPK/TOC/ITOC/@UTF reader is a format reference, not archive precedence or native FileLoad lifetime proof.
- REA current main `8ff3570430ad682061b7932b9953d45b904cb487`; binary diagnostics guide blob `76da9004df7abee2831a2b1d9bc32e99d0e03f1c`; supported targets blob `b4fad121e917a1a6eb148e72c4ac1daef7d95265`. Its offline ELF diagnostics require caller-supplied pwntools on Linux x64 for ELF64 little-endian AArch64; this is static evidence only.
- Game-specific original Switch v1.70 main is tracked at `original/atmosphere/contents/0100FA10190A0000/exefs/main`, Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes, expected SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.

## Why this implementation

The previous pinned report enumerated 4,055 ADRP references: 89 to the table page and 3,966 to pages containing candidate pointer cells. Ten target-page references and 421 pointer-page references reached the 256-state budget. It found 271 unique static pointer loads, one ambiguous load, 10,485 call barriers, and 4,210 out-of-window edges. The report correctly refused to claim complete CFG coverage.

The old state identity included the complete branch-site history. Two paths that arrived at the same PC with identical tracked address registers and identical origin chains were therefore counted as separate states, causing path-history explosion without changing any later memory-address calculation.

## Implementation

- State identity now includes PC, tracked address values, dynamic index terms, origin chain, and a boolean branch-reachable class.
- The branchless and branch-reachable variants remain separate. Distinct register values or origin chains never merge.
- Multiple branch histories that reach the same semantic state share one representative path; the report increments `equivalent_branch_histories_merged` and explicitly marks branch-path witness enumeration non-exhaustive.
- Calls remain clobber barriers. Out-of-window branches, unknown aliases, BSS/heap cells, and function extents remain unresolved.
- New synthetic tests prove (1) two different branch histories can merge without losing a reachable table store, and (2) distinct effective addresses at a CFG join remain separate.

## Falsifiable acceptance criteria

On the exact pinned main, the report must:
1. Preserve every prior linear witness and all seven indexed-read sites.
2. Never merge states with different effective addresses or different origin chains.
3. Report representative-only branch witnesses whenever equivalent branch histories merge.
4. Reduce state-budget exhaustion without hiding any budget or undecodable condition.
5. Keep producer identity, complete writer census, runtime table values, BR X2 target, object type, callback/destructor, ownership/lifecycle, lock/unlock, async, rollback/unbind, native consumer ABI, archive precedence, Uzuy, and gameplay flags false.

## Source URLs and exact content pins

- [NSC-ModManager 2.1.2.1 release](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1); current main is one commit ahead of the tag, but parser and skill-model Git blobs are identical between tag and main.
- [NSC-ModManager XfbinParser.cs](https://github.com/TheLeonX/NSC-ModManager/blob/502c38d3ee832509f9ee3951b7d3339826538fec/XfbinParser.cs), blob `faf79d588fd8beb3f5761faebedd2252853b2f2b`; [SkillCustomizeParamModel.cs](https://github.com/TheLeonX/NSC-ModManager/blob/502c38d3ee832509f9ee3951b7d3339826538fec/Model/SkillCustomizeParamModel.cs), blob `6a891e237d27fdf01336f806dbef8767d609a304`.
- [NSC-Toolbox 2.1.2.1 release](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1); current main is one commit ahead of the tag, but relevant parser/editor/model Git blobs are identical between tag and main.
- [NSC-Toolbox XfbinParser.cs](https://github.com/TheLeonX/NSC-Toolbox/blob/789fe96f99cdaa77f952b90b563c6e3f49b6d697/XfbinParser.cs), blob `86c63708edf2698b5bc1c2a54c0480cce014b525`; [SkillEditorModel.cs](https://github.com/TheLeonX/NSC-Toolbox/blob/789fe96f99cdaa77f952b90b563c6e3f49b6d697/Model/SkillEditorModel.cs), blob `e165471682e4a7aed91094ef07f92df271f31639`.
- [UltimateStormAPI current MovesetPlus.cpp](https://github.com/TheLeonX/UltimateStormAPI/blob/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc/xinput9_1_0/MovesetPlus.cpp), blob `d7c5dbbebd60415f8d304321f083897658a86146`; [comparison parent](https://github.com/TheLeonX/UltimateStormAPI/blob/1c3460573fa70b595e6bfa70e52f83f1c3f74f12/xinput9_1_0/MovesetPlus.cpp), blob `e96af51210e96926a7bdaa70c44b6645f1a2b2b6`.
- [PyCriCodecs CPK parser](https://github.com/t-wy/PyCriCodecs/blob/755055ee7b056c9c1aefc6505a3daa3e45e2e111/PyCriCodecs/cpk.py), blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; [UTF parser](https://github.com/t-wy/PyCriCodecs/blob/755055ee7b056c9c1aefc6505a3daa3e45e2e111/PyCriCodecs/utf.py), blob `d1662d140a48cae37a6696213ee441aed4076edb`.
- [REA binary diagnostics](https://github.com/morluto/rea/blob/8ff3570430ad682061b7932b9953d45b904cb487/docs/guides/native/binary-diagnostics.md), blob `76da9004df7abee2831a2b1d9bc32e99d0e03f1c`; [supported targets](https://github.com/morluto/rea/blob/8ff3570430ad682061b7932b9953d45b904cb487/docs/guides/native/supported-targets.md), blob `b4fad121e917a1a6eb148e72c4ac1daef7d95265`.
- [Pinned Switch v1.70 original main](https://github.com/Anovvoldigoad/switchmain/blob/63c4cf76fe0daf6e9fcec6cc1fe854b21e0402b1/original/atmosphere/contents/0100FA10190A0000/exefs/main), Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes, SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.

The ModManager 2.1.2.1 release notes add Switch Projectiles Target. The current PC API source adds `TakeOverEnemyProjectiles` command 29; `SetProjectileDeflection` cases 27/28 existed in the parent. The new command's Windows mutex/time and PC engine state are not Switch ABI proof.

## CI

- Targeted FileLoad run [46116650719](https://github.com/Anovvoldigoad/switchmain/actions/runs/46116650719), job 140891888185: COMPLETED SUCCESS; raw log inspected. Success marker: `PINNED_FILELOAD_TABLE_CFG_PASS adrp_refs 4055 direct_accesses 72 indexed_accesses 7 branch_path_writes 32 static_pointer_cells 214 loaded_aliases 271 NO_ABI_NO_OWNER_NO_ARCHIVE_PRECEDENCE_NO_UZUY_CLAIM`. Artifact 15251304501, ZIP SHA256 `f4fcd676bfe1dd434326cc6c462e29c7aa096a5b2618e1e6ba08073d65d28e2b`, report JSON SHA256 `6dbb3f0f3583778d5216ff01c880f3e2b6dcc9890b4f29348eccbd36705c6f36`.
- Broad foundation run [46116650641](https://github.com/Anovvoldigoad/switchmain/actions/runs/46116650641), job 140891888072: COMPLETED SUCCESS; raw log inspected. 74 JSON proof files, artifact 15251649607, ZIP SHA256 `7de286c39c04324821d060ae85c1b5ebe960e7aafd78b7eb9d3796acb564f159`. The release-flag guard JSON SHA256 is `fc0e84147e3cd026dc61cfa795330b7fc847de2890cd99878e7b506324dd4773` and confirms all three release flags false.
- Historical failed runs were inspected: 46115143110/140887161526 and 46115280209/140887598475 were strict ADRP-budget failures; 46115452263/140888141364 was a missing page-key lookup; 46115503191/140888301215 asserted full CFG completeness despite a state budget. The current implementation records these limits instead of masking them, and both current workflows pass.

Measured result: equivalent-state dedup reduced references reaching the 256-state budget from 431 to 47 (89.1%); 2 target-page and 45 pointer-page references remain budget-exhausted. It merged 7,510 equivalent branch histories and therefore reports branch-path witnesses as representative-only. Six additional bounded reads were exposed at `0x116bf70` and `0x116bfc8` for slot offsets `0x80`, `0x88`, and `0x90`. The target CFG and pointer alias trace remain incomplete; no producer, consumer ABI, ownership, callback, archive precedence, Uzuy or gameplay claim is made.

Sakura aura107, Event236 marker `0x4E53 +0x2A`, Event236 without marker, and all three release flags remain unchanged/false.
