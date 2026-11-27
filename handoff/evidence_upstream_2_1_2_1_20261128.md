# Research-first evidence: upstream 2.1.2.1 and recursive FileLoad proof

Date: 2026-11-28  
Branch: `port/full-api-v170`  
Pre-change HEAD: `e6f0601aaf0d9897192532eeaddcac888de74348`

## Primary-source pins and findings

| Source | Exact ref | Inspected source blobs / result |
|---|---|---|
| [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag `502c38d3ee832509f9ee3951b7d3339826538fec`, published 2026-08-30 | Release notes add **Switch Projectiles Target** |
| [NSC-ModManager 2.1.2.0](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0) | tag `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`, published 2026-08-28 | Release notes add **Start Deflect / Stop Deflect** |
| Repo-pinned NSC-ModManager source | `276116ebf5ba398a867793cb02ee6c33c0927645` | `SkillCustomizeParamModel.cs` blob `6a891e237d27fdf01336f806dbef8767d609a304`; `SkillCustomizeParamViewModel.cs` `ced6d805b207fae16cf68df87e23744608d6562b`; `SpSkillCustomizeParamModel.cs` `2b518f6eeb9ef97895517582e393a2adf9ee6da0`; `SpSkillCustomizeParamViewModel.cs` `dcfccabe2edb8dd1bc1f0a05be81bdaefb9d517e` |
| [UltimateStormAPI 2.1.2.1 source](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | commit `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, parent `1c3460573fa70b595e6bfa70e52f83f1c3f74f12` | `MovesetPlus.cpp` latest blob `d7c5dbbebd60415f8d304321f083897658a86146`, parent blob `e96af51210e96926a7bdaa70c44b6645f1a2b2b6`; `MovesetPlus.h` latest `74f6ff6c0243a01d7e49d8565c9933089b8c7a2c`, parent `d177fb8dc1af164f19bbaca0abf968d6bc0d8dc9` |
| [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | tag `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; previous `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31` | `SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`; `SkillEditorViewModel.cs` `870af492c41f26c2aab07c216b6fa5fd00ac2cbf` |
| [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111` | `cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; `utf.py` `d1662d140a48cae37a6696213ee441aed4076edb` |
| [REA](https://github.com/Black-Star-Pen/REA/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4) | commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4` | README blob `474ecfbec32c2ef86e5d0cf17837892d5b07335a`; CLI/evidence doc `35f686aa26ba850b56e8a74df648f47d99a164e3` |

### Upstream feature delta — verified, not ported

- The latest ModManager release is 2.1.2.1; its previous 2.1.2.0 release documents Start/Stop Deflect, while 2.1.2.1 adds Switch Projectiles Target.
- The pinned PC ModManager source commit is 276116e, a descendant of the 2.1.2.1 release commit. The inspected model/viewmodel blobs are the same across the release tags; this release delta is not evidence of a changed binary parser ABI.
- The pinned PC API source is the exact 2.1.2.1 UltimateStormAPI commit a2d0f22. Comparing its parent to a2d0f22 shows the new command-29 takeover path in `MovesetPlus.cpp`: it tracks recently active projectile objects, queues a 250 ms takeover window, and transfers owner/collision identity. The prior source already contains the deflection enable/disable command path. This is Windows x64 implementation behavior only. Its object offsets, hook signatures, atomics, mutexes, and lifetime assumptions are **not** portable evidence for Switch v1.70.
- NSC-Toolbox's inspected skill editor model/viewmodel blobs are identical across 2.1.2.0 and 2.1.2.1. The Toolbox release note does not establish a parser or Switch consumer ABI change.
- PyCriCodecs documents CRI CPK/UTF chunk parsing and TOC/ITOC extraction. It is a format reference only; it cannot establish Switch CPK registration precedence or native FileLoad ownership.
- REA supplies a reproducible evidence workflow; it is methodology, not a source of target-specific ABI facts.

## Game-specific pinned bytes

- Original Switch v1.70 main: `original/atmosphere/contents/0100FA10190A0000/exefs/main`
- Git blob: `8af900db0d7003255b4ddb3cbd1289cd5a15458e`
- Size: 27,701,509 bytes
- Required SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- Latest pre-change HEAD Foundation run/job: `46067348811 / 140735790410`, completed SUCCESS; raw log inspected. Artifact `15231472880` (336,355 bytes, SHA256 `e54fa121ad5303061fc4f979c6eb71074475ff97871037e70e62eabae1417223`).

Exact caller bytes already verified by the SHA-guarded original-main test:

| Address | Little-endian word | Instruction |
|---|---|---|
| `0x116f278` | `e0c30091` | `add x0, sp, #0x30` |
| `0x116f280` | `126d0294` | `bl 0x120a6c8` |
| `0x116f284` | `e1c30091` | `add x1, sp, #0x30` |

At `0x120a6c8`, the bounded callee saves incoming X19 at entry-SP -8; it restores that slot at `0x120a724`. The remaining uncertainty is not this local pair: it is the nested callees' register/stack effects and writes through pointers whose provenance is not yet established.

## This implementation slice

The analyzer previously summarized recursive child proofs with counts and unknown-write rows but discarded the child's raw reachable AArch64 instruction words and the exact pointer offsets passed into that nested call. The updated proof object now retains:
- input register-to-entry-SP offsets, input SP delta/trust, and protected slots at the callsite;
- the child's initial offsets and bounded reachable instruction rows, each including the little-endian raw word, mnemonic, operands, and memory base/index;
- child return states and unresolved CFG edges.

This is evidence serialization only. It does not relax any barrier, infer a function extent, or mark X19 preserved. Synthetic tests assert exact raw word `081000f9` for `str x8, [x0, #0x20]`, the stack-derived input offset, return SP, and protected slot. The original-main regression also requires every nested child report to retain a complete 4-byte instruction word.

## Falsifiable next hypothesis

For each child call under `0x120a6c8`, compare its exact input-register offsets and raw memory operands against the inherited protected entry-SP slot `-8`. A child can be accepted only if every reachable return restores X19, SP is balanced and trusted, and every write is either proven disjoint or otherwise proven not to alias the protected slot. Unknown bases/indexes, out-of-window branches, indirect calls, cycles, and no-reachable-return windows remain barriers. Even a fully proven X19 stack-preservation result would not prove object type, ownership, callback contract, async lifetime, rollback/unbind/destructor, archive precedence, or Switch gameplay compatibility.
