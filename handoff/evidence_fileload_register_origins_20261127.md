# FileLoad indexed-register reaching definitions — 2026-11-27

## Research-first source pins

- NSC-ModManager release 2.1.2.1 was published 2026-08-30 at tag commit 502c38d3ee832509f9ee3951b7d3339826538fec; release 2.1.2.0 tag commit a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983. The 2.1.2.1 release note adds “Switch Projectiles Target”; 2.1.2.0 adds Start/Stop Deflect. Relevant upstream ModManager source commit inspected: 276116ebf5ba398a867793cb02ee6c33c0927645, including Properties/Program.cs blob 682f9a0129b8a1cf73d77b408786891c5129a29c. That file's ME_NSC_LIST is a PC editor name/index table and contains no text hit for the new release-note names; it does not establish Switch event dispatch or ABI.
- NSC-Toolbox tag 2.1.2.1 commit 789fe96f99cdaa77f952b90b563c6e3f49b6d697 and 2.1.2.0 commit dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31. The three inspected parser/editor files are byte-identical across tags: ViewModel/PRMEditorViewModel.cs blob 6a1ffac148942abe1c542fe12c960a7296bb99a6, Model/PRMEditorModel.cs blob 4115be4b8b7cb95e8bc56f05dff1e5016c592bd9, and Properties/Program.cs blob 9d5f3e0dfa4ed51cf7924b503081a87b12146f64. This is no evidence of a parser format or Switch ABI change between these tags.
- CRI reference: t-wy/PyCriCodecs commit 755055ee7b056c9c1aefc6505a3daa3e45e2e111; cpk.py blob 2ed2cbb2c6112124013ab52755dba8a443e91306 and utf.py blob d1662d140a48cae37a6696213ee441aed4076edb. Used only to cross-check CRI CPK @UTF metadata structure; this slice does not parse or mutate a game CPK.
- REA reference: Black-Star-Pen/REA commit 0386efd1e1dfa41af41f804a6be56c6f5b7615d4, docs/binary-diagnostics.md blob b58b8d04dc799813d0ebe0dcd4889560c707553c. Its own documented supported targets exclude AArch64. It is a methodology reference only, not the decoder for this Switch main.
- Target: repository-tracked Switch v1.70 original/atmosphere/contents/0100FA10190A0000/exefs/main, Git blob 8af900db0d7003255b4ddb3cbd1289cd5a15458e, 27,701,509 bytes; required SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. The parent Foundation push artifact (run 45977479925, job 140432739883, artifact 15188585337) contains the SHA-guarded bounded FileLoad report. The report records 166 reachable instructions, 10 SP-based accesses, 5 indexed operands, and window SHA256 b396fb643d979d6b303862d8096110f8d0d6cdbc5aeea091f4d29bb14a60b412.

## Original bytes and falsifiable register hypotheses

The first indexed memory operation occurs before the first call barrier:

| PC | little-endian word | decoded instruction | register role |
|---|---|---|---|
| 0x116f418 | 089001d0 | adrp x8, #0x4371000 | X8 page-relative definition |
| 0x116f41c | 587080b9 | ldrsw x24, [x2, #0x70] | X24 receives a signed 32-bit memory value; X2 is entry-live in this bounded path |
| 0x116f424 | 083145f9 | ldr x8, [x8, #0xa60] | X8 receives a pointer-like value loaded from global slot 0x4371a60 |
| 0x116f430 | 137978f8 | ldr x19, [x8, x24, lsl #3] | indexed read |

Falsifiable expectations:
1. At 0x116f430, the unique reaching definition of X8 is the LDR at 0x116f424; that LDR's source X8 definition is the ADRP at 0x116f418.
2. The unique reaching definition of X24 is LDRSW at 0x116f41c; its base X2 is entry-live (not overwritten in this bounded path).
3. The register-origin report never claims the loaded X8 pointer or X24 numeric value is resolved.
4. Later indexed operations after opaque calls must show call-clobber or post-call local reaching definitions. The analysis deliberately invalidates all X0–X30 and SP origins after a call rather than assuming AAPCS64 callee-saved behavior.
5. A branch merge preserves multiple reaching definitions; Wn writes replace the canonical Xn definition; SP-derived pointer definitions retain the path SP delta.

## Implementation and regression scope

native_fileload_sp_cfg.py now performs a bounded forward reaching-definition analysis over the already-built CFG states. Each indexed operand receives per-state base/index reaching definitions and one-level source-register origins. Definitions retain original PC, little-endian instruction word, mnemonic, operand text, and pre-instruction SP delta. Calls clobber every GPR origin; no numeric values, object types, ownership, or function ABI are inferred.

tests/test_native_fileload_sp_cfg.py adds synthetic positive/negative/boundary checks for an ADRP→LDR base chain, LDRSW index source, opaque-call clobber, branch merge, W-register canonicalization, and SP-derived base. The pinned original-main test asserts the exact first operand def-use PCs and keeps numeric-value/ABI/ownership flags false.

## Evidence boundary

This is read-only static host analysis over pinned original executable bytes plus synthetic instruction fixtures. It is not an emulated ARM64 execution, runtime consumer proof, object ownership/lifetime proof, callback/lock/async/rollback/unbind/destructor proof, archive precedence proof, or Uzuy gameplay test. No runtime hook, original-main byte, CPK, Sakura aura107, Event236 marker/unmarked asset, or release flag is changed.