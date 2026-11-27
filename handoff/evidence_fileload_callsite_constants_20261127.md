# FileLoad callsite constants and expanded direct-callee windows — 2026-11-27

## Scope and safety boundary

Read-only evidence from the exact Naruto Storm Connections Switch v1.70 original `main`. No hook, patch, ABI assumption, ownership claim, archive-precedence claim, or gameplay claim is introduced.

Pinned image SHA256:
`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

Pinned FileLoad CFG window SHA256:
`b396fb643d979d6b303862d8096110f8d0d6cdbc5aeea091f4d29bb14a60b412`

The existing Foundation artifact for run `46000351128` (job `140510105439`) contains 22 reachable direct `BL` callsites. Two callsites target the same bounded code address:

| Callsite | Instruction | Direct target | X1 definition | Exact value |
|---|---|---|---|---:|
| `0x116f520` | `bl #0x120661c` | `0x120661c` | `0x116f518: mov w1, #5` | 5 |
| `0x116f5c0` | `bl #0x120661c` | `0x120661c` | `0x116f5b8: mov w1, #5` | 5 |

The instruction word at each definition is little-endian `a1008052` (AArch64 `MOV W1, #5`). A W-register write zero-extends the architectural X-register, so the register value is exactly 5 at each callsite. This is a machine-level constant only; it does **not** identify the semantic parameter or establish the callee ABI.

The analyzer change deliberately recognizes only a single reaching definition that is a direct `MOV Wn/Xn, #imm`. It does not propagate through arithmetic or register-to-register MOV, does not collapse branch-merged definitions, and does not retain constants across opaque calls. Immediate values are width-masked (32/64-bit) and W-register values are reported with their architectural zero-extended X value.

The direct-callee inventory now includes the 11 reachable calls after the existing pre-status checkpoint and bounded windows for nine previously unreported direct targets. The target `0x120661c` is analyzed once even though two callsites reach it. A bounded 0x200-byte window is not asserted to be a function extent. Decode failures remain explicit unresolved records. Register preservation, native consumer ABI, object ownership/lifetime, callback/lock/async/rollback/unbind/destructor behavior, and archive precedence remain false/unproven.

## Research-first source comparison

- NSC-ModManager release tag 2.1.2.0: commit `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`.
- NSC-ModManager release tag 2.1.2.1: commit `502c38d3ee832509f9ee3951b7d3339826538fec`; one commit ahead. The release notes mention Switch Projectiles Target, but the relevant `Model/SkillCustomizeParamModel.cs` blob `6a891e237d27d7f01336f806dbef8767d609a304` and `ViewModel/SkillCustomizeParamViewModel.cs` blob `ced6d805b207fae16cf68df87e23744608d6562b` are unchanged between tags. The changed source is not evidence of a new Switch engine ABI.
- NSC-Toolbox release tag 2.1.2.0: commit `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31`.
- NSC-Toolbox release tag 2.1.2.1: commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`. `Model/SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639` and `Properties/Program.cs` blob `9d5f3e0dfa4ed51cf7924b503081a87b12146f64` are unchanged. The tag diff is localization/costume UI, not a new skill-event parser layout. Therefore no numeric Switch Projectiles Target or Start/Stop Deflect function index is inferred.
- CRI CPK/UTF reference: PyCriCodecs commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; `PyCriCodecs/cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`, `PyCriCodecs/utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`. Used only as format reference; it does not establish Switch runtime consumer behavior.
- REA commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4` was checked as a general reverse-engineering methodology source, not as a CRI CPK implementation and not as game-specific ABI evidence.

## Falsifiable regression contract

1. Exact original-main SHA256 is checked before producing the pinned report.
2. Both original callsites above must reach target `0x120661c`, and X1 must have a single direct immediate definition at the specified PC with width 32 and unsigned value 5.
3. Synthetic 32/64-bit immediate boundaries cover `Wn=-1`, `Xn=-1`, `Wn=0xffff`, and an ordinary 64-bit immediate.
4. Branch-merged immediate definitions, register-to-register MOV, and post-call clobbers must not be mislabeled as a direct immediate constant.
5. The call-target census must retain all 11 later direct callsites and add nine unique bounded target windows, including `0x120661c`; no preservation or function-boundary claim is allowed.

## CI state at code commit creation

Pending until the code commit's Foundation, compressed PRM, factory/multi-mod, and MovesetPlus push workflows complete and their original job logs are inspected.
