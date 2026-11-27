# FileLoad registration-table direct-callee evidence — 2026-11-28

## Research-first primary sources

| Source | Exact ref | Inspected source and result |
|---|---|---|
| [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag commit 502c38d3ee832509f9ee3951b7d3339826538fec | Release notes add Switch Projectiles Target. Model/SkillCustomizeParamModel.cs Git blob 6a891e237d27fdf01336f806dbef8767d609a304. |
| [NSC-ModManager 2.1.2.0](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0) | tag commit a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983 | Release notes add Start Deflect / Stop Deflect. SkillCustomizeParamModel.cs and XfbinParser.cs blobs are identical to 2.1.2.1: 6a891e237d27fdf01336f806dbef8767d609a304 and faf79d588fd8beb3f5761faebedd2252853b2f2b. |
| [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | tag commit 789fe96f99cdaa77f952b90b563c6e3f49b6d697 | Release notes add Switch Projectiles Target. Model/SkillEditorModel.cs Git blob e165471682e4a7aed91094ef07f92df271f31639. |
| [NSC-Toolbox 2.1.2.0](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.0) | tag commit dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31 | SkillEditorModel.cs and XfbinParser.cs blobs are identical to 2.1.2.1: e165471682e4a7aed91094ef07f92df271f31639 and 86c63708edf2698b5bc1c2a54c0480cce014b525. |
| [PyCriCodecs CPK reference](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | commit 755055ee7b056c9c1aefc6505a3daa3e45e2e111 | cpk.py Git blob 2ed2cbb2c6112124013ab52755dba8a443e91306 parses CPK header and UTF metadata, then follows TOC/ITOC/HTOC/GTOC/ETOC offsets; utf.py blob d1662d140a48cae37a6696213ee441aed4076edb parses @UTF/EUTF. Generic archive-format reference only. |
| [REA static-analysis methodology](https://github.com/morluto/rea/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4) | pinned guide commit 0386efd1e1dfa41af41f804a6be56c6f5b7615d4; current upstream HEAD c4bc2f7fcb73882f638b9d9a31fd49156bd902f6 | docs/ci-analysis.md documents retaining machine-readable evidence and original diagnostics in CI. Methodology only, not game-specific ABI evidence. |
| Pinned Switch v1.70 original main | Git blob 8af900db0d7003255b4ddb3cbd1289cd5a15458e, 27,701,509 bytes | Required SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. Foundation workflow reads this exact tracked file. |
| Local prior FileLoad evidence | handoff/evidence_fileload_registration_target_20261128.md | Exact caller target is a bounded direct BL 0x116b8a4 -> 0x116b390; caller load at 0x116b8a0 is ldr x0,[x8,#0x28]. Existing table-loop/zero-store facts remain static observations only. |

## Falsifiable hypothesis and byte-backed scope

The verified registration-target CFG has one direct BL at 0x116b8a4 to 0x116b390. At 0x116b8a0, X0 is loaded from the 64-bit memory operand [X8,#0x28]; the runtime type/meaning of that value is unknown. This slice tests whether the target window contains direct or indirect calls, returns, memory accesses, stack accesses and bounded exits. It also inventories raw aligned-text B/BL words targeting the callee; those candidates are not function-boundary or callback proof.

The trace is deliberately bounded to [0x116b390,0x116b590). It does not claim that this is a complete function. Any direct call is a non-walked barrier; any indirect target stays unresolved. The output cannot establish whether the call is a destructor, callback, release routine, synchronous/asynchronous operation, rollback, unbind, or consumer. It cannot establish lock ownership or archive precedence.

## Implementation

- Source: tools/portlib/native_fileload_registration_callee.py
- Test: tests/test_native_fileload_registration_callee.py
- Foundation workflow: .github/workflows/verify-port-foundation.yml
- Parent HEAD: a859b4454fe7f8b1b18c5930bba38c483e7b7b6c
- Source blob: 3bf733dc6d3368a7569d79853bef557fd330a03d
- Test blob: b5d6190d3dd8e50ad29f1507c45734f8a0767504
- Workflow blob: 68320ad7f4e5b3a728fe06a55528cc6225d6376b
- CI state at commit preparation: PENDING_CI
- Release flags remain false; no hook is added.
