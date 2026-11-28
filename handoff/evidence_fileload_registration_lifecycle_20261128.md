# FileLoad registration-helper and alternate-tail trace — PENDING_CI

Date: 2026-11-28  
Parent HEAD: \`4dcd6ecc307655d63b08acf538e2a3b3811c9f3d\`  
Original Switch v1.70 main Git blob: \`8af900db0d7003255b4ddb3cbd1289cd5a15458e\`  
Required SHA256: \`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9\`

## Research-first primary sources

- [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), tag \`502c38d3ee832509f9ee3951b7d3339826538fec\`; previous 2.1.2.0 tag \`a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983\`. Full source compare has one non-generated C# source change in \`ViewModel/TitleViewModel.cs\`; no SkillCustomizeParam/XFBIN parser delta.
- [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1), tag \`789fe96f99cdaa77f952b90b563c6e3f49b6d697\`; previous \`dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31\`. Exact source blobs: \`SkillEditorModel.cs\` e165471682e4a7aed91094ef07f92df271f31639, \`SkillEditorViewModel.cs\` 870af492c41f26c2aab07c216b6fa5fd00ac2cbf, \`ConditionPrmModel.cs\` 2827ca9e484eafb0c7435f066d42ff3e9345e17c, \`XfbinParser.cs\` 86c63708edf2698b5bc1c2a54c0480cce014b525. The inspected skill/XFBIN parser files are unchanged across the release tags.
- [UltimateStormAPI 2.1.2.1](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc), commit \`a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc\`, parent \`1c3460573fa70b595e6bfa70e52f83f1c3f74f12\`; \`MovesetPlus.cpp\` blob d7c5dbbebd60415f8d304321f083897658a86146. The 2.1.2.1 diff adds command 29, \`TakeOverEnemyProjectiles\`: it queues recently active projectile pointers for a 250 ms takeover window under a Windows mutex; later PC hooks transfer owner/collision identity. This Windows x64 implementation is not Switch ABI evidence.
- [PyCriCodecs CPK reference](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111), commit \`755055ee7b056c9c1aefc6505a3daa3e45e2e111\`: \`cpk.py\` blob 2ed2cbb2c6112124013ab52755dba8a443e91306 and \`utf.py\` blob d1662d140a48cae37a6696213ee441aed4076edb. It reads CRI CPK metadata and TOC/ITOC/HTOC/GTOC/HGTOC offsets; format reference only, not Switch archive precedence.
- [REA](https://github.com/morluto/rea/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4), commit \`0386efd1e1dfa41af41f804a6be56c6f5b7615d4\`: evidence-workflow methodology only, not target ABI.
- Original game bytes are pinned in this repository at \`original/atmosphere/contents/0100FA10190A0000/exefs/main\`, blob \`8af900db0d7003255b4ddb3cbd1289cd5a15458e\`, 27,701,509 bytes.

## Vertical slice

New read-only analyzer \`tools/portlib/native_fileload_registration_lifecycle.py\` traces the bounded 0x290 helper, its 24-byte record writes, the relocated code-pointer candidate 0x116b888 and its 64-slot cleanup loop, the alternate tail PLT at 0x12f49b0 and the index-error target 0x12155a0. It emits machine-readable JSON from the exact original main. It does not infer callback/destructor identity, imported implementation, runtime ownership, lock/lifetime/async semantics, rollback/unbind or archive precedence.

An isolated workflow runs only this new test. Existing Foundation/Factory/Compressed/Moveset workflows receive path filters so unrelated PASS suites are not rerun for this FileLoad-only change.

## CI

Pending for code commit. Do not promote this note to verified until the direct push run completes, its original job log is inspected, and the uploaded JSON artifact is checked. All release flags remain false; no runtime hook is added.
