# FileLoad guard state and registration-helper candidate — PENDING_CI

Date: 2026-11-28  
Branch: `port/full-api-v170`  
Parent HEAD: `261e4aab417b1aebaaeddb9a83160a46dc812255`

## Research-first primary sources

| Source | Exact ref | Inspected blob / finding |
|---|---|---|
| [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`, published 2026-08-30 | Release adds Switch Projectiles Target. |
| [NSC-ModManager 2.1.2.0](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0) | tag commit `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`, published 2026-08-28 | Release adds Start Deflect / Stop Deflect. |
| Repo-pinned NSC-ModManager | commit `276116ebf5ba398a867793cb02ee6c33c0927645` | `SkillCustomizeParamModel.cs` blob `6a891e237d27fdf01336f806dbef8767d609a304`, identical at 2.1.2.0 and 2.1.2.1. This release delta does not prove a parser or Switch ABI change. |
| [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; previous `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31` | `SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`, identical across the two tags. |
| [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111` | `cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; `utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`. CPK TOC/ITOC are parsed through UTF; this is format evidence, not Switch archive precedence. |
| [REA](https://github.com/Black-Star-Pen/REA/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4) | commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4` | README blob `474ecfbec32c2ef86e5d0cf17837892d5b07335a`; `docs/cli.md` blob `35f686aa26ba850b56e8a74df648f47d99a164e3`. REA is an evidence workflow/methodology, not target-specific ABI evidence. |
| [Pinned Switch v1.70 main](https://github.com/Anovvoldigoad/switchmain/blob/port/full-api-v170/original/atmosphere/contents/0100FA10190A0000/exefs/main) | Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes | Required SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`; enforced by the new test. |

## Current upstream delta versus the repository pin

- ModManager 2.1.2.0 documents Start/Stop Deflect; 2.1.2.1 adds Switch Projectiles Target.
- The inspected ModManager model blob and Toolbox skill-editor blob are unchanged across the two tags. The release feature delta therefore cannot be treated as evidence of a changed parser ABI.
- The pinned PC API source remains Windows x64 evidence. Its object offsets, hooks, mutexes, callback assumptions and lifetime are not Switch evidence.
- PyCriCodecs confirms generic CPK/UTF structure only. It does not identify the Switch loader's archive precedence or FileLoad lifecycle.

## Exact original-main observations

The preceding verified HEAD `261e4aab417b1aebaaeddb9a83160a46dc812255` resolves two nested imports:

| Callsite | PLT | GOT slot | DT_JMPREL record | Relocation / symbol |
|---|---|---|---|---|
| `0x116b7e0` | `0x12f3690` | `0x2141ef8` | `0x198f5c0` | `R_AARCH64_JUMP_SLOT`, symbol index 6, `__cxa_guard_acquire` |
| `0x116b818` | `0x12f36a0` | `0x2141f00` | `0x198f5d8` | `R_AARCH64_JUMP_SLOT`, symbol index 7, `__cxa_guard_release` |

The symbol names are relocation evidence only; their provider module, implementation and runtime binding are not established.

The new analyzer checks the exact AArch64 words and decodes the address materializations:
- `ADRP X8; ADD X8,#0x7d8` at `0x116b7b4/0x116b7b8` and `ADRP X19; ADD X19,#0x7d8` at `0x116b7d4/0x116b7d8` both produce guard candidate `0x43717d8`.
- `MOV X0,X19` immediately precedes both guard PLT calls; the register value is `0x43717d8` at both callsites.
- The early and late return paths materialize X0 as `0x43717e0`, exactly guard + 8.
- Explicit stores use X1 copied from X19 or X19 directly: `0x43717e0..0x43717e8` (8 bytes), `0x43717e8..0x43717f8` (16 bytes), and `0x43717f8..0x4371800` (8 bytes). The test checks their mapped image region is BSS before recording non-alias evidence against the parent's entry-SP-8 slot.

The bounded direct helper call `0x116b810 -> 0x290` has a separate registration-table candidate shape:
- X0 is loaded from pointer cell `0x215d2b0`; its raw value and relocation records are emitted without assuming a callback identity.
- X1 is the static-object address `0x43717e0`; X2 is PC-relative address `0x1eb3000`.
- The helper loads base/limit pointer cells `0x2143460` / `0x2143468`, uses an atomic counter at `0x21620d8`, materializes stride `0x18`, and stores X8/X1/X2 in a 24-byte record. Pointer-cell runtime values, function extent and helper semantics remain unresolved. Do not label this as `__cxa_atexit` or a destructor without proof.

## Falsifiable tests and safety boundary

Synthetic tests cover positive ADRP/ADD and ADRP/LDR decoding, negative signed page deltas, wrong register/shift/opcode, BSS end and cross-region boundaries, zero-width/negative addresses. The original-main test rejects a changed SHA and requires exact instruction words, both relocation-backed symbol names, all three explicit BSS store ranges and the 24-byte helper record shape.

No runtime hook, ownership claim, destructor claim, callback claim, lock semantic, async completion, rollback/unbind, archive precedence or native consumer ABI is added. Existing recursive X19 call barrier remains false. All release flags remain false.

## CI

PENDING: the new code/test commit and Foundation push run must complete; inspect the raw job log and proof artifact before promoting this note to verified.
