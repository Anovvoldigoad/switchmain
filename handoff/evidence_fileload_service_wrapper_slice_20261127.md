# FileLoad service dependency and wrapper execution evidence — 2026-11-27

## Research-first source pins

- NSC-ModManager latest release 2.1.2.1, published 2026-08-30: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1
  - Tag commit: `502c38d3ee832509f9ee3951b7d3339826538fec`.
  - The repository's pinned PC manager source `276116ebf5ba398a867793cb02ee6c33c0927645` has parent exactly `502c38d3ee832509f9ee3951b7d3339826538fec` (commit message `2.1.2.1 update`).
  - SkillCustomizeParamViewModel blob `ced6d805b207fae16cf68df87e23744608d6562b` and SkillCustomizeParamModel blob `6a891e237d27fdf01336f806dbef8767d609a304` are identical at 2.1.2.0 tag `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983` and 2.1.2.1. This is a PC parser/editor comparison only.
  - The 2.1.2.1 release notes advertise Switch Projectiles Target; the 2.1.2.0 notes advertise Start/Stop Deflect. No new Event236 numeric ID or Switch consumer ABI is inferred from release notes.

- NSC-Toolbox latest release 2.1.2.1: https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1
  - Tag commit: `789fe96f99cdaa77f952b90b563c6e3f49b6d697`.
  - SkillEditorViewModel blob `870af492c41f26c2aab07c216b6fa5fd00ac2cbf` and SkillEditorModel blob `e165471682e4a7aed91094ef07f92df271f31639` are identical at 2.1.2.0 tag `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31` and 2.1.2.1.
  - Therefore the new release feature is not evidence of a changed editor parser or Switch runtime contract.

- CRI/CPK reference: https://github.com/t-wy/PyCriCodecs
  - Pinned commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`.
  - `PyCriCodecs/cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; `PyCriCodecs/utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`.
  - These are format-level CPK/@UTF references, not Switch engine ownership or archive precedence proof.

- Independent RE workflow reference: https://github.com/Black-Star-Pen/REA
  - Pinned commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4`.
  - README blob `474ecfbec32c2ef86e5d0cf17837892d5b07335a`; CLI guide blob `35f686aa26ba850b56e8a74df648f47d99a164e3`.
  - REA is a generic evidence workflow tool, not a CRI parser or Switch ABI source.

## Exact Switch v1.70 bytes

- Repository: https://github.com/Anovvoldigoad/switchmain
- Branch at investigation start: `port/full-api-v170`
- Parent HEAD: `5efd93a9d5d23ab96f3fd7a4404a46e50153c6ac`
- Original main: `original/atmosphere/contents/0100FA10190A0000/exefs/main`
- Git blob: `8af900db0d7003255b4ddb3cbd1289cd5a15458e` (27,701,509 bytes)
- Required whole-file SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

The already SHA-pinned status helper at `0x120661c` passes X0+0x18 to dispatch entries `0x1215358` and `0x1215374`. Both dispatch paths then execute `ADD X0,X0,#8` before tail-branching to their wrapper targets, so the wrapper's X0 is the original status object +0x20. The wrapper's owner/count fields are therefore at original object +0x28/+0x2c, while the dispatch gate is read at original object +0x40. The bounded dispatch window `0x1215358..0x12153d8` (128 bytes, SHA256 `57ceb7351df052e968a1431e70c39812c323d0880d00d36380c01814af58976e`) contains:
- `0x1215364 B 0x1158c90`
- `0x1215380 B 0x1158d10`
- `0x12153a8 BL 0x1158d30`

The 256-byte target window `0x1158c90..0x1158d90` has SHA256 `c173105388fd40288927c87c40b2882abf9a97ff4fcae5f229af50a1cac07461`. It shows:
- `0x1158c90` saves LR/X19/X20, calls `0x12f4cf0`, conditionally calls `0x12f50e0`, compares a W32 field at X19+8, conditionally calls `0x12a35b4`, then writes a W32 value to X19+8 and increments/writes the W32 count at X19+12.
- `0x1158d10` decrements the W32 field at X0+12; a negative result returns without writing, a nonzero result returns after writing the decremented count, and zero clears X0+8 then branches to `0x12a35bc`.
- `0x1158d30` is a single RET at this exact target address.

These instructions support a falsifiable *owner-token/count wrapper* hypothesis. They do not identify the two token providers or prove that `0x12a35b4`/`0x12a35bc` are OS mutex acquire/release primitives. Bounded windows are not function boundaries.

## New implementation

- Extend the SHA-pinned FileLoad report with three bounded dependency windows:
  - `0x12a35b4..0x12a36b4` (entry observations at `0x12a35b4` and `0x12a35bc`)
  - `0x12f4cf0..0x12f4df0`
  - `0x12f50e0..0x12f51e0`
- Record exact bytes, disassembly, register/memory operands, bounded CFG traces, and whole-text direct B/BL inbound edges for all four dependency addresses. Never infer function extent or semantics from the chosen windows.
- The emulated test models the dispatch's observed +8 X0 adjustment: wrapper X0 = caller subobject +8; owner/count are wrapper X0 +8/+12. The first test attempt incorrectly used the pre-adjustment subobject as the owner/count base; this was corrected.
- Add a Unicorn test that executes the original dispatch and wrapper instructions at `0x1215358`, `0x1215374`, `0x1158c90`, and `0x1158d10`. Only four leaf targets (`0x12f4cf0`, `0x12f50e0`, `0x12a35b4`, `0x12a35bc`) are intercepted with deterministic test stubs.
- Regressions cover first acquisition, same-token recursive acquisition, non-final release, final release, zero-count underflow, zero context result, different owner token, and 32 status-helper trials. This verifies the literal owner/count wrapper state machine under modeled leaf returns; it is not a multithreaded lock test.

## Explicit unresolved evidence

`thread_token_provider_semantics_verified=false`, `mutex_primitive_semantics_verified=false`, `concurrent_behavior_verified=false`, `native_consumer_abi_verified=false`, `ownership_lifecycle_async_rollback_unbind_destructor_verified=false`, `archive_precedence_verified=false`, `Uzuy_tested=false`. No runtime hook is added. The three release flags remain false.
