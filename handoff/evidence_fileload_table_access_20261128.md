# FileLoad 64-slot table direct-reference census — IMPLEMENTED_AWAITING_CI

Date: 2026-11-28
Parent branch HEAD: 9ea102fe95646d1d595ec33335aa16a563e5ef97
Target original main Git blob: 8af900db0d7003255b4ddb3cbd1289cd5a15458e, 27,701,509 bytes
Required original main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

## Research-first primary sources (independently re-read)

- NSC-ModManager 2.1.2.1: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1, tag commit 502c38d3ee832509f9ee3951b7d3339826538fec; prior 2.1.2.0 a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983. The release compare has one non-generated source change in ViewModel/TitleViewModel.cs; inspected Model/SkillCustomizeParamModel.cs blob 6a891e237d27fdf01336f806dbef8767d609a304 and XfbinParser.cs blob faf79d588fd8beb3f5761faebedd2252853b2f2b are byte-identical across tags.
- NSC-Toolbox 2.1.2.1: https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1, tag commit 789fe96f99cdaa77f952b90b563c6e3f49b6d697; prior 2.1.2.0 dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31. Inspected SkillEditorModel.cs blob e165471682e4a7aed91094ef07f92df271f31639, ConditionPrmModel.cs blob 2827ca9e484eafb0c7435f066d42ff3e9345e17c, and XfbinParser.cs blob 86c63708edf2698b5bc1c2a54c0480cce014b525 are byte-identical across tags.
- UltimateStormAPI 2.1.2.1: https://github.com/TheLeonX/UltimateStormAPI/commit/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc, commit a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc, parent 1c3460573fa70b595e6bfa70e52f83f1c3f74f12. MovesetPlus.cpp blob d7c5dbbebd60415f8d304321f083897658a86146 differs from 2.1.2.0 blob e96af51210e96926a7bdaa70c44b6645f1a2b2b6: command case 29 calls TakeOverEnemyProjectiles. The implementation uses Windows mutexes, GetTickCount64, a 250 ms expiry and cached PC projectile pointers. This is PC Windows x64 source, not Switch ARM64 ABI or ownership evidence.
- Pinned NSC-Toolbox Moveset name catalog: https://github.com/TheLeonX/NSC-Toolbox/blob/6f780cb6814f07e03c16b3e78d97dde4e4368983/Properties/Program.cs, blob 9d5f3e0dfa4ed51cf7924b503081a87b12146f64: 300 NSC names with a 289-name NS4 prefix. Command-29 dispatch is a runtime parameter of meTest, not an additional function-name index; engine function IDs remain unverified.
- PyCriCodecs CPK: https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111, commit 755055ee7b056c9c1aefc6505a3daa3e45e2e111: cpk.py blob 2ed2cbb2c6112124013ab52755dba8a443e91306 parses TOC/ITOC/HTOC/GTOC/HGTOC/ETOC offsets and sizes; utf.py blob d1662d140a48cae37a6696213ee441aed4076edb parses @UTF row/string/data offsets. This is format evidence, not game-specific archive precedence.
- REA binary diagnostics: https://github.com/morluto/rea/blob/0386efd1e1dfa41af41f804a6be56c6f5b7615d4/docs/binary-diagnostics.md, commit 0386efd1e1dfa41af41f804a6be56c6f5b7615d4: linked addresses, symbols and relocations are static evidence; runtime load base and actual binding must remain separate/unset absent runtime data.
- Local evidence: handoff/evidence_fileload_registration_lifecycle_20261128.md; latest verified code commit 2b06a49730dc3bdf9816cc7f4f984231aa34b4fe; isolated push run 46086093686, job 140795884030, completed SUCCESS with raw log inspected. Current branch documentation HEAD before this slice was 9ea102fe95646d1d595ec33335aa16a563e5ef97; that docs-only HEAD had no workflow run. No earlier pending runs were found for the latest four code heads.

## New reproducible slice

New analyzer tools/portlib/native_fileload_table_access.py scans every aligned AArch64 ADRP word in original text whose decoded page equals 0x4371000. For each candidate it follows only a 0x100-byte bounded linear window, tracks ADRP/ADD-immediate/MOV register address chains, and inventories direct memory operands overlapping [0x4371800,0x4371a00). It also scans both dynamic RELA tables for relocation destinations inside the table and signed addends pointing into it.

The exact original-main checks require the first 64-bit slot load at 0x116b8a0 to resolve to 0x4371800, and the 16 existing STP Q0,Q0 clear writes at 0x116b8c4..0x116b900 to cover the 512-byte region in reverse 0x20-byte steps. Any direct writes outside this known clear sequence are emitted as candidates, not assigned producer semantics.

Synthetic regressions cover positive direct store/load/pair-store, exact exclusive-end boundary, branch barrier, register clobber, malformed ranges, relocation destination/addend and RELA bounds/overlap. The original main is SHA256-pinned. CI is pending.

## Explicit limits

This is a static direct-reference census only. It does not resolve indexed effective addresses, indirect register aliases, heap objects, function extents, the dynamic BR X2 value at 0x116b3d0, callback/vtable/destructor identity, ownership, locks, async, rollback/unbind, allocator implementation, archive precedence, emulated ARM64 or Uzuy. No hook is added. full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false.
