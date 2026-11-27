# FileLoad X19 stack-alias provenance — 2026-11-28

## Scope and safety

This slice narrows the static proof boundary for the direct callee at 0x120a6c8. It does not identify a C++ type, ownership contract, callback ABI, lock, async lifecycle, rollback, unbind, destructor, archive precedence, or a Switch runtime consumer. No hook or game write is authorized by this evidence.

Implementation parent:  ba91387833c699418cc931d15d420e0c22b66802
Branch:  port/full-api-v170
Implementation CI state at authoring:  PENDING_CI

## Research-first source pins

| Primary source | Exact ref | Relevant blob / observation |
|---|---|---|
| [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag commit 502c38d3ee832509f9ee3951b7d3339826538fec | Release notes add Switch Projectiles Target |
| [NSC-ModManager 2.1.2.0](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0) | tag commit a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983 | Release notes add Start Deflect / Stop Deflect |
| NSC-ModManager Model/SkillCustomizeParamModel.cs | both tags above | blob 6a891e237d27fdf01336f806dbef8767d609a304 at both tags |
| NSC-ModManager ViewModel/SkillCustomizeParamViewModel.cs | both tags above | blob ced6d805b207fae16cf68df87e23744608d6562b at both tags |
| [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/tree/789fe96f99cdaa77f952b90b563c6e3f49b6d697) | tag commit 789fe96f99cdaa77f952b90b563c6e3f49b6d697 | relevant parser/editor files below |
| NSC-Toolbox Model/SkillEditorModel.cs | 2.1.2.1 and 2.1.2.0 | blob e165471682e4a7aed91094ef07f92df271f31639 at both tags |
| NSC-Toolbox ViewModel/SkillEditorViewModel.cs | 2.1.2.1 and 2.1.2.0 | blob 870af492c41f26c2aab07c216b6fa5fd00ac2cbf at both tags |
| [PyCriCodecs CPK](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111/PyCriCodecs/cpk.py) | commit 755055ee7b056c9c1aefc6505a3daa3e45e2e111 | cpk.py blob 2ed2cbb2c6112124013ab52755dba8a443e91306 |
| PyCriCodecs UTF | same commit | utf.py blob d1662d140a48cae37a6696213ee441aed4076edb |
| [REA](https://github.com/Black-Star-Pen/REA/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4) | commit 0386efd1e1dfa41af41f804a6be56c6f5b7615d4 | README blob 474ecfbec32c2ef86e5d0cf17837892d5b07335a |

The relevant ModManager and Toolbox parser/editor files listed above are byte-identical across 2.1.2.0 and 2.1.2.1. The release-note feature delta is therefore not evidence of a parser ABI change. The repository's PC source pins remain ModManager commit 276116ebf5ba398a867793cb02ee6c33c0927645 and PC API source commit a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc. None of these PC/CRI references establish a Switch engine ABI.

## Pinned Switch bytes and prior CI

Original Switch v1.70 main:

- Repository path: original/atmosphere/contents/0100FA10190A0000/exefs/main
- Git blob: 8af900db0d7003255b4ddb3cbd1289cd5a15458e
- Size: 27,701,509 bytes
- Required SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

Prior parent HEAD ba91387833c699418cc931d15d420e0c22b66802 completed all four push workflows; original job logs were read:

| Workflow | Run | Job |
|---|---:|---:|
| Foundation | 46059295804 | 140709365877 |
| Compressed PRM | 46059295779 | 140709366278 |
| Factory multi-mod | 46059295836 | 140709365821 |
| MovesetPlus | 46059295771 | 140709365935 |

Foundation artifact 15228421515 (foundation-ba913.zip) SHA256 2faea0bc25db8b784796e4309c97cecaff65b694e1f084eed78dae952619522f. The artifact's FileLoad caller window is 0x116f09c..0x116f2a0, SHA256 e18c0fcb01a040df2b232820813420313e623c5747bd0734507920507ba0775d.

## Reproduced byte facts

At the caller window:

| PC | Little-endian word | Instruction |
|---|---|---|
| 0x116f278 | e0c30091 | add x0, sp, #0x30 |
| 0x116f280 | 126d0294 | bl 0x120a6c8 |
| 0x116f284 | e1c30091 | add x1, sp, #0x30 |

The bounded callee window 0x120a6c8..0x120a8c8 has SHA256 60189963ab42120388f1b88d443ad722ae48275830ea07d2edd415140ee54f12 and 25 reachable instructions in the prior artifact.

Relevant callee sequence:

- 0x120a6c8: stp x30, x19, [sp, #-0x10]! — saves incoming X19 at entry-SP -8.
- 0x120a6cc: mov x19, x0 — X19 receives the caller's SP-relative pointer, entry-SP +0x30.
- Nested direct calls:
  - 0x120a6d0 -> 0x116b698
  - 0x120a6e8 -> 0x1188104
  - 0x120a6f0 -> 0x1170f7c
  - 0x120a6f8 -> 0x1160c64
- 0x120a724: ldp x30, x19, [sp], #0x10.
- 0x120a728: ret.

The visible stores through X19 have these entry-SP-relative ranges when X19 is entry-SP +0x30:

| PC | Store | Effective range |
|---|---|---|
| 0x120a6e4 | str x8, [x19] | [+0x30,+0x38) |
| 0x120a700 | str w8, [x19,#0x1d0] | [+0x200,+0x204) |
| 0x120a708 | stp xzr,xzr,[x19,#0x1a8] | [+0x1d8,+0x1e8) |
| 0x120a710 | stp xzr,xzr,[x19,#0x1c0] | [+0x1f0,+0x200) |
| 0x120a714 | str xzr,[x19,#0x1b8] | [+0x1e8,+0x1f0) |
| 0x120a718 | strb wzr,[x19,#0x1d4] | [+0x204,+0x205) |
| 0x120a71c | strb w8,[x19,#0x1d5] | [+0x205,+0x206) |
| 0x120a720 | str wzr,[x19,#0x1d8] | [+0x208,+0x20c) |

These local ranges are disjoint from the saved incoming-X19 slot [-8,0). This does not by itself prove the nested callees cannot alias that slot.

## Falsifiable proof condition

The new analyzer obtains X0's stack-relative origin from the call-input dataflow at 0x116f280, propagates only exact 64-bit MOV/ADD/SUB-immediate pointer offsets, and recursively checks each direct callee. A nested call is accepted only if every bounded reachable return preserves X19, restores its entry SP, and has no unknown or overlapping write to the inherited protected slot. Byte/halfword/pair widths are included; unknown base/index, indirect call, out-of-window edge, cycle, or budget exhaustion remains a barrier.

The hypothesis is falsified if any child fails one of those conditions. Even a successful register-preservation proof would establish only a bounded register/stack fact, not object type, ownership, callback contract, lifetime, or native consumer compatibility.

## Regression coverage added

- Positive nested direct call with a stack-derived X0 pointer and disjoint stores.
- Exact 8-byte overlap with the saved slot.
- One-byte partial overlap.
- 16-byte STP XZR,XZR overlap.
- Boundary-adjacent non-overlapping store.
- Unknown pointer base.
- Unbalanced nested SP.
- Recursive call cycle.
- Original-main assertion for the exact X0 definition at 0x116f278.
