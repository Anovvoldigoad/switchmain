# FileLoad call-preservation proof without platform ABI assumptions — 2026-11-27

## Research-first primary-source pins

- NSC-ModManager latest release 2.1.2.1, published 2026-08-30: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1, tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`. Prior 2.1.2.0 tag: `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`. Relevant PC source blobs unchanged across tags: `Model/SkillCustomizeParamModel.cs` `6a891e237d27fdf01336f806dbef8767d609a304`, `ViewModel/SkillCustomizeParamViewModel.cs` `ced6d805b207fae16cf68df87e23744608d6562b`, `Properties/Program.cs` `682f9a0129b8a1cf73d77b408786891c5129a29c`.
- NSC-Toolbox latest release 2.1.2.1, published 2026-08-30: https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1, tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`. Prior 2.1.2.0 tag: `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31`. Relevant model/editor blobs unchanged: `Model/SkillEditorModel.cs` `e165471682e4a7aed91094ef07f92df271f31639`, `ViewModel/SkillEditorViewModel.cs` `870af492c41f26c2aab07c216b6fa5fd00ac2cbf`, `Properties/Program.cs` `9d5f3e0dfa4ed51cf7924b503081a87b12146f64`. Release-note changes do not establish Switch ABI.
- CRI CPK/@UTF reference: https://github.com/t-wy/PyCriCodecs at commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; `cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`, `utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`. Format reference only.
- Independent RE methodology reference: https://github.com/Black-Star-Pen/REA at commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4`; README blob `474ecfbec32c2ef86e5d0cf17837892d5b07335a`, binary diagnostics guide blob `b58b8d04dc799813d0ebe0dcd4889560c707553c`. Not a Switch ABI or AArch64 decoder.

## Pinned Switch input and prior authentic evidence

- Branch parent: `b63f6ec01e9e66d01451d6d076220913b8249bb1`.
- Original Switch v1.70 main: `original/atmosphere/contents/0100FA10190A0000/exefs/main`; Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes; required SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- Parent HEAD four completed push workflows with raw job logs inspected: Foundation `46026476677/140599058069`, compressed PRM `46026476733/140599058042`, factory `46026477131/140599059347`, MovesetPlus `46026476837/140599058732`.
- Foundation artifact `15211614727`, 294,528 bytes, ZIP SHA256 `3ed4501a3d6cc9607618f115006b05fc09c6c02388d7446f65d8b74ab997356d`. It confirms FileLoad captures `X2 -> X20` at `0x116f434`, `X1 -> X22` at `0x116f438`, and later observes X20 at `0x116f51c` / `0x116f5bc`, X22 at `0x116f5ac`.
- The prior object-register report explicitly assumed AAPCS64 callee-saved X20/X22 survive calls. That assumption was not established by the Switch image. The direct-callee inventory shows mixed cases: `0x116d3c0` and `0x12155a0` have no X20/X22 writes in their bounded windows; `0x11709a0` and `0x1170fb0` write those registers; other targets include nested, indirect or out-of-window transfers.

## Implemented conservative proof

- `prove_register_preservation` analyzes a fixed 0x200-byte window at a direct target. A register is preserved only when every reachable path returns inside that window, no instruction writes the tracked register, there are no indirect calls/terminators or out-of-window/undecodable edges, and every nested direct call recursively satisfies the same proof.
- A bounded window is not asserted to be a function extent. Register writes, stack spill/restore patterns, indirect calls, tail/out-of-window branches, cycles and exhausted budgets remain unresolved. No AAPCS64 or cross-OS calling convention is assumed.
- The object-register analyzer now treats each call as a clobber unless that exact direct callee is proven to preserve the register. It separates entry-register capture from later status/guard observations rather than carrying X20/X22 through calls by ABI convention.
- Synthetic regressions cover a clean leaf, a recursively proven nested leaf, register write, indirect call, recursion, out-of-window branch, truncated window, and call-barrier dataflow.

## Evidence boundary

Read-only static analysis of the SHA-pinned original Switch main plus synthetic instruction fixtures. It does not prove object type, pointer validity, allocation, ownership, destructor, callback, async completion, rollback, unbind, actual mutex semantics, archive precedence, native consumer ABI for the nine parser families, or Uzuy gameplay. No runtime hook, original game byte, CPK, Sakura aura107, Event236 marked/unmarked asset, or release flag is changed.

Initial state: PENDING_CI. All four push workflows and raw logs for the new HEAD must be checked before this slice is CI-verified.
