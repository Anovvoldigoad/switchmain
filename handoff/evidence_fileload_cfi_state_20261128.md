# FileLoad CFI state evidence — 2026-11-28

## Reproduction inputs

- Repository: https://github.com/Anovvoldigoad/switchmain
- Branch at implementation: \`port/full-api-v170\`
- Implementation commit: \`48b742b865dbdc17d3d6f4265dc6a8b2b81a81d3\`
- Parent: \`2133abb9534561eeacf47ffeff54a08e99339880\`
- Original Switch v1.70 main Git blob: \`8af900db0d7003255b4ddb3cbd1289cd5a15458e\`
- Original main size: 27,701,509 bytes
- Original main SHA256: \`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9\`
- Source blob: \`c6028a9e28fe644cea5a798bb40b3c7b4b78cbb8\`
- Test blob: \`c27d2a276bb0eb0592d88fe220546d845ecfbf0e\`

## Primary-source cross-check

1. NSC-ModManager 2.1.2.1 tag commit \`502c38d3ee832509f9ee3951b7d3339826538fec\`; project pin \`276116ebf5ba398a867793cb02ee6c33c0927645\`. Parser/model blobs match exactly:
   - \`XfbinParser.cs\`: \`faf79d588fd8beb3f5761faebedd2252853b2f2b\`
   - \`Model/SkillCustomizeParamModel.cs\`: \`6a891e237d27fdf01336f806dbef8767d609a304\`
   - \`Model/SpSkillCustomizeParamModel.cs\`: \`2b518f6eeb9ef97895517582e393a2adf9ee6da0\`
2. NSC-Toolbox 2.1.2.1 tag commit \`789fe96f99cdaa77f952b90b563c6e3f49b6d697\`; project pin \`6f780cb6814f07e03c16b3e78d97dde4e4368983\`. Parser/editor/model blobs match:
   - \`XfbinParser.cs\`: \`86c63708edf2698b5bc1c2a54c0480cce014b525\`
   - \`Model/SkillEditorModel.cs\`: \`e165471682e4a7aed91094ef07f92df271f31639\`
   - \`Model/SkillCustomizeParamModel.cs\`: \`1b45c89ca9d36b6db874603cdc28290d2b019f25\`
   - \`Model/SpSkillCustomizeParamModel.cs\`: \`b684c33e2acec0ec5527864b86899e6277a15e53\`
3. UltimateStormAPI project pin \`a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc\`, \`MovesetPlus.cpp\` blob \`d7c5dbbebd60415f8d304321f083897658a86146\`; comparison parent \`1c3460573fa70b595e6bfa70e52f83f1c3f74f12\`, blob \`e96af51210e96926a7bdaa70c44b6645f1a2b2b6\`. Cases 27/28 and \`SetProjectileDeflection\` exist in both. Case 29 / \`TakeOverEnemyProjectiles\` exists only in the pin. It reads side from a version-specific player offset, locks a Windows mutex, queues recent projectile handles, and expires them after 250 ms using \`GetTickCount64\`. This is PC Windows behavior; no Switch ABI is implied.
4. PyCriCodecs commit \`755055ee7b056c9c1aefc6505a3daa3e45e2e111\`: \`cpk.py\` blob \`2ed2cbb2c6112124013ab52755dba8a443e91306\`, \`utf.py\` blob \`d1662d140a48cae37a6696213ee441aed4076edb\`.
5. REA commit \`0386efd1e1dfa41af41f804a6be56c6f5b7615d4\`: \`docs/binary-diagnostics.md\` blob \`b58b8d04dc799813d0ebe0dcd4889560c707553c\`. The inspected diagnostics profile does not support AArch64, so it was not used as a Switch-main decoder.

Source links:
- https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1
- https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1
- https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc
- https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111
- https://github.com/morluto/rea/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4

## Binary layout and CFI interpretation

- GNU \`.eh_frame_hdr\` is in original main segment index 1, segment VA \`0x12f6000\`.
- Header file offset \`0x8ad0a8\`, VA \`0x1ba30a8\`, SHA256 \`6d7ff19ab079d7c609426068ad42bfa18ed9f89f9763421e1fe1d2fb4c38be63\`.
- \`.eh_frame\` VA \`0x1c49fd0\`; 85,474 validated FDE records.
- Pointer encodings: eh_frame pointer \`0x1b\`, FDE count \`0x03\`, table \`0x3b\`.
- The new interpreter retains CIE/FDE instruction byte ranges and SHA256 values, executes a bounded DW_CFA subset, and fails closed on unsupported opcodes and \`DW_CFA_set_loc\`. Expression bytecode is preserved as hex, not evaluated.
- Six exact PCs decode: helper entry \`0x116b390\`, helper \`BR X2\` \`0x116b3d0\`, registration-walk candidate \`0x116b888\`, second table-path start \`0x116b90c\`, and table-path calls \`0x116b8a4\` / \`0x116b928\`.
- Counts: decoded 6, unsupported 0, unmapped 0, ambiguous 0.
- FDE coverage intervals:
  - helper: \`0x116b390..0x116b3f0\`
  - table path 0: \`0x116b888..0x116b90c\`
  - table path 1: \`0x116b90c..0x116b990\`
- At \`0x116b3d0\`, \`0x116b8a4\`, and \`0x116b928\`: CFA = SP + 0x20; X19 recovery = CFA - 8; LR/X30 recovery = CFA - 0x20.
- These are static unwind recovery rules, not runtime register captures. The FDE intervals remain unwind coverage, not proven function identity.

## Regression and CI

- Synthetic positive: CFA register+offset, X19 save rule, location advance, restore rule.
- Synthetic negative: unsupported DW_CFA opcode and truncated operand.
- Synthetic boundary: query at FDE end is rejected.
- Authentic pinned-main assertions: all six target PCs must decode; no unsupported/unmapped/ambiguous targets.
- Targeted run \`46100321645\`, job \`140841047537\`: COMPLETED SUCCESS; raw log inspected. Artifact \`15245162374\`, ZIP SHA256 \`ac07da627905706da9e45f0a86b1620d1d32a3e6ee47059d0d2331e442a25101\`; report JSON SHA256 \`432a57d02bd7056861a45642d5bb2b96d56c8dae430e0de47a59cf6e9c3a1be9\`.
- Broad foundation run \`46100321670\`, job \`140841047578\`: COMPLETED SUCCESS; raw log inspected; 74 JSON proof files, artifact \`15245303059\`, ZIP SHA256 \`aaf920f3a76d53937a8f4faefb913eb9e430fe6b13329b538ca2f29d794868b5\`.
- No ABI, ownership, callback, lock/unlock, async lifetime, rollback, unbind, destructor, archive precedence or gameplay claim is made.

## P32 packaging correction

- Historical run \`46099189607\` failed at artifact collection because three optional root files were absent; the module had already compiled.
- Workflow fix commit \`fbd13b35c07e88642ba3e5afb5818e678176807a\`, parent \`48b742b865dbdc17d3d6f4265dc6a8b2b81a81d3\`, generates a factual README and omits absent optional files.
- Run \`46100950488\`, build job \`140843020466\`: COMPLETED SUCCESS; raw log inspected. Artifact \`15245441982\`, 101,471 bytes, ZIP SHA256 \`2b5cd550145ae661200e1ce574eff0c6688d611c1e6b9d9dd96b804e73e8e9d1\`.
- Included \`subsdk9\`: 128,446 bytes, SHA256 \`fec2462e48e6960b225692f9ab2c68a481c21e049d800d51d91d09574a82b504\`.
- Build artifact only; no Uzuy/gameplay test.
