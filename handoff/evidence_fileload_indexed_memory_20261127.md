# FileLoad indexed-memory alias evidence — 2026-11-27

## Research gate and source pins

- NSC-ModManager release 2.1.2.0 (2026-08-28), tag commit `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`: release notes add PRM functions Start Deflect and Stop Deflect. Release 2.1.2.1 (2026-08-30), tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`: adds Switch Projectiles Target. Primary sources: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0 and https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1
- NSC-Toolbox tags 2.1.2.0 `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31` and 2.1.2.1 `789fe96f99cdaa77f952b90b563c6e3f49b6d697`. At both tags, the PRM parser/editor files are byte-identical by Git blob: `ViewModel/PRMEditorViewModel.cs` `6a1ffac148942abe1c542fe12c960a7296bb99a6`, `Model/PRMEditorModel.cs` `4115be4b8b7cb95e8bc56f05dff1e5016c592bd9`, and `Properties/Program.cs` `9d5f3e0dfa4ed51cf7924b503081a87b12146f64`. Thus the release-note function additions do not correspond to a changed parser implementation in these files. The Toolbox wiki maps Event 236 Param1 27/28/29 to Start Deflect, Stop Deflect, and Switch Projectiles Target; this is PC tooling/event metadata, not proof of Switch engine ABI: https://github-wiki-see.page/m/TheLeonX/NSC-Toolbox/wiki/Custom-Moveset-Functions-in-ModdingAPI
- CRI reference: t-wy/PyCriCodecs commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; `PyCriCodecs/cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`, `utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`. The reference parses CPK TOC/ITOC using offsets/sizes in the CPK @UTF table and validates @UTF row/column structure. It is a format cross-check only; no CPK or runtime behavior is changed in this slice.
- REA binary-analysis reference: Black-Star-Pen/REA commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4`; `docs/binary-diagnostics.md` blob `b58b8d04dc799813d0ebe0dcd4889560c707553c`. Used as a methodology reference for retaining original offsets/ranges and explicit unknowns, not as evidence about this game.
- Target original v1.70 main is tracked at `original/atmosphere/contents/0100FA10190A0000/exefs/main`, Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes. Required SHA256 remains `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`; the existing test hashes the bytes before analyzing them. Prior HEAD Foundation log independently emitted this digest and `PINNED_FILELOAD_SP_CFG_PASS 166 10 NO_CONSUMER_ABI`.

## Reproduced issue and byte layout

ARM64 register-offset memory operands compute an address from base + index (optionally shifted/extended) + displacement. The previous analyzer used only `mem.disp` for SP-based accesses and for SP-derived alias stores. This could falsely turn an unknown indexed address into a constant stack slot or falsely declare an indexed store disjoint from a candidate slot.

The exact little-endian A64 words below were assembled with Clang 17.0.0 (`clang --target=aarch64-linux-gnu`) and disassembled with LLVM objdump:

| Word | Instruction | Relevant operand |
|---|---|---|
| `0xd10043ff` | `sub sp, sp, #16` | entry SP delta = -16 |
| `0xf8226be1` | `str x1, [sp, x2]` | index x2; displacement 0 |
| `0xf8626be3` | `ldr x3, [sp, x2]` | index x2; displacement 0 |
| `0xf8657be4` | `ldr x4, [sp, x5, lsl #3]` | index x5; shift 3 |
| `0x910083e3` | `add x3, sp, #32` | X3 = SP + 32 |
| `0xf8256864` | `str x4, [x3, x5]` | unknown index can alias any stack slot |
| `0xf94007e2` | `ldr x2, [sp, #8]` | immediate-only positive control |

Falsifiable regressions:
1. A same-index SP store/load pair must **not** produce a stack write/read candidate while X2 is unproven.
2. A shifted index operand must be recorded with `effective_address_resolved=false`.
3. A store through X3=SP+32 with an unknown X5 index must invalidate a purportedly disjoint witness to SP+8.
4. Existing immediate-only SP accesses must retain their prior exact offsets and positive candidate behavior.

## Change scope and evidence boundary

The analyzer now records indexed memory operands with base/index/displacement, leaves effective addresses unresolved, marks SP-indexed accesses ambiguous, and terminates candidate witnesses when an indexed store uses a non-SP SP-derived base. SP writeback is also made unknown if an indexed SP memory operand is ever surfaced. The original-main JSON report includes the indexed operand inventory.

This is read-only static evidence only. It does not prove execution, register values, object ownership, allocator contracts, callback, locks, async completion, rollback, unbind/destructor, archive precedence, native consumer ABI, or Uzuy gameplay. No runtime hooks, original main edits, CPK writes, Sakura aura107 changes, or Event236 marker/unmarked changes.


## CI verification — 2026-11-27

Code commit `df9a3e1e41db4d1b2063f2ac7b31e5adc6ef3dea` (parent `840f92aa7d6dc5b812a07c2fc8c4ae8589b58ac3`) was verified by GitHub Actions push workflows on the exact code HEAD:
- Foundation run [45976679056](https://github.com/Anovvoldigoad/switchmain/actions/runs/45976679056), job `140430025592`: COMPLETED SUCCESS; raw log inspected. It emitted `PINNED_FILELOAD_SP_CFG_PASS 166 10 NO_CONSUMER_ABI` and `RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS 26 NO_UZUY_PROOF`. The FileLoad CFG step completed successfully.
- Compressed PRM run [45976679041](https://github.com/Anovvoldigoad/switchmain/actions/runs/45976679041), job `140430025502`: COMPLETED SUCCESS; raw log inspected.
- Factory multi-mod run [45976679120](https://github.com/Anovvoldigoad/switchmain/actions/runs/45976679120), job `140430025333`: COMPLETED SUCCESS; raw log inspected.
- MovesetPlus multi-mod run [45976679117](https://github.com/Anovvoldigoad/switchmain/actions/runs/45976679117), job `140430026222`: COMPLETED SUCCESS; raw log inspected.
- Foundation artifact `PORT_FOUNDATION_PROOFS_NOT_A_GAMEPLAY_RELEASE`, ID `15187631793`, 263930 bytes.

This verifies host Python/Capstone static analysis and the original-main SHA guard only. It is not an emulated ARM64 test of this analyzer, native engine consumer proof, or Uzuy gameplay.
