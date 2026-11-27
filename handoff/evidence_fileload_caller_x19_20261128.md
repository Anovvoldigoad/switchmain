# FileLoad caller X19 provenance with exact-callee preservation — 2026-11-28

## Research-first pins

- NSC-ModManager latest release 2.1.2.1: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1, tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`. The immediately prior 2.1.2.0 release: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0, tag commit `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`. Release notes differ: 2.1.2.0 adds Start Deflect / Stop Deflect; 2.1.2.1 adds Switch Projectiles Target. The latest ModManager source tree contains the pinned PC editor model/viewmodel sources; this task does not infer a Switch event ABI from those PC release notes.
- NSC-Toolbox 2.1.2.1 tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; 2.1.2.0 tag commit `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31`. The previously pinned SkillEditorModel, SkillEditorViewModel and Program source blobs are unchanged between these tags (respectively `e165471682e4a7aed91094ef07f92df271f31639`, `870af492c41f26c2aab07c216b6fa5fd00ac2cbf`, `9d5f3e0dfa4ed51cf7924b503081a87b12146f64`). This is PC editor source evidence only.
- CRI CPK/@UTF reference: https://github.com/t-wy/PyCriCodecs, commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; `cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`, `utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`.
- Independent reverse-engineering methodology reference: https://github.com/Black-Star-Pen/REA, commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4`; binary diagnostics guide blob `b58b8d04dc799813d0ebe0dcd4889560c707553c`. Not an AArch64 decoder or game ABI source.
- Pinned Switch v1.70 input: `original/atmosphere/contents/0100FA10190A0000/exefs/main`, Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes, SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`. The tracked exefs tree contains this original main only (plus the separate P128 reference main); no additional original Switch NSO provider module is available in this repository tree.

## Exact caller bytes and falsifiable hypothesis

The unique direct FileLoad call remains `BL 0x116f404` at `0x116f29c` (word LE `5a000094`). Its caller window is `[0x116f09c, 0x116f2a0)`, SHA256 `e18c0fcb01a040df2b232820813420313e623c5747bd0734507920507ba0775d`.

- X1 is defined at `0x116f284`: `add x1, sp, #0x30` (word LE `e1c30091`).
- X2 is defined at `0x116f294`: `mov x2, x19` (word LE `e20313aa`).
- X19 is loaded on two conditional paths at `0x116f1a4` and `0x116f1b4`, each `ldr x19, [x21, #0x40]` (word LE `b32240f9`).

Falsifiable hypothesis: the X19 value reaching the FileLoad call can be narrowed to those one or both loads only if every intervening direct BL on the path has a positive, exact-target bounded callee preservation proof. The proof is deliberately stricter than AAPCS64: the callee window must have only returning paths, no X19 writes, no unresolved indirect calls/terminators, no out-of-window exits, and all nested direct callees recursively pass. A failed or missing proof becomes a call barrier. No calling convention is assumed.

Direct calls scanned before the FileLoad callsite:
`0x116f1c0 -> 0x116d3c0`, `0x116f1cc -> 0x120661c`, `0x116f1e8 -> 0x1215d28`, `0x116f1f0 -> 0x116b698`, `0x116f22c -> 0x1161030`, `0x116f23c -> 0x12f37f0`, `0x116f248 -> 0x12f3760`, `0x116f254 -> 0x12f3760`, `0x116f25c -> 0x12f36d0`, `0x116f280 -> 0x120a6c8`.

## Implementation

The bounded caller analyzer now tracks X1, X2 and X19. X1/X2 retain the existing conservative call barriers. X19 may cross a direct call only when `native_fileload_call_targets.prove_register_preservation` proves the exact target under the no-ABI bounded rule above. A mismatched proof target is rejected. The machine-readable artifact records all ten direct call targets and their full per-target proof reports, and retains all unresolved origins as call barriers.

Synthetic tests cover a positive preserved leaf, absent/negative proof, mismatched target, and conditional merge retaining both X19 definitions. Original-main tests assert the exact ten direct calls and keep numeric value, pointer type, ownership, lifetime, consumer ABI and runtime flags false.

## Evidence boundary

Static host analysis over the SHA-pinned original main plus synthetic instruction fixtures only. It does not establish the loaded X19 value, pointer validity/type, caller function extent, object ownership/lifetime, destructor, callback, async completion, rollback, unbind, imported runtime provider, archive precedence, native consumer ABI for the nine parser families, or Uzuy gameplay. No hook, original main byte, CPK, Sakura aura107, Event236 marked/unmarked asset, or release flag is changed. CI state is pending until the new HEAD's authentic push job log and artifact are inspected.


## CI failure analysis and regression correction — 2026-11-28

The first X19 implementation HEAD `04cd926fe4af8144e53fc7eb92c9c5096ce38fd0` failed the synthetic map expectation; the corrected HEAD `5187073633307e43985684325ebdce9821948849` advanced through the original-main SHA check and X19 proof construction but failed at the hard-coded `expected_calls` list in `tests/test_native_fileload_inbound_args.py`. Exact push job: run `46046833811`, job `140668067037`; the raw log was inspected. The other three workflows on that HEAD completed successfully: factory run/job `46046833823/140668067179`, compressed PRM `46046833807/140668067777`, and MovesetPlus `46046833905/140668067827`; raw logs were inspected.

The test no longer duplicates a manually transcribed call-target list. It independently decodes each original little-endian instruction word in the SHA-pinned caller window using the A64 `BL` encoding (`op[31:26] == 0b100101`, signed `imm26 << 2`) and compares that inventory with the per-call preservation proofs. Synthetic controls cover forward and backward BL, exclusion of unconditional B, malformed/unaligned rows, ordering, and invalid boundary. This retains exact callsite/target checking without trusting the same production helper or a stale transcription.

The correction is pending push CI. No consumer ABI, pointer value/type, ownership/lifecycle, callback/async/rollback/unbind/destructor, archive precedence, or Uzuy claim is added. Release flags remain false.
