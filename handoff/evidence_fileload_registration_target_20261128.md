# FileLoad registration code-pointer target trace — PENDING_CI

Date: 2026-11-28  
Branch: `port/full-api-v170`  
Parent HEAD: `9975550ae11657970ae8905a808aa0360ad36710`

## Research-first primary sources

| Primary source | Exact ref / commit | Inspected code / byte evidence |
|---|---|---|
| [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`, published 2026-08-30 | Release adds **Switch Projectiles Target** (change owner of enemy projectiles). |
| [NSC-ModManager 2.1.2.0](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0) | tag commit `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`, published 2026-08-28 | Release adds **Start Deflect / Stop Deflect** (deflect projectiles back to sender). |
| ModManager source comparison | 2.1.2.1 vs 2.1.2.0 | `SkillCustomizeParamModel.cs` blob `6a891e237d27fdf01336f806dbef8767d609a304`, `SkillCustomizeParamViewModel.cs` `ced6d805b207fae16cf68df87e23744608d6562b`, `SpSkillCustomizeParamModel.cs` `2b518f6eeb9ef97895517582e393a2adf9ee6da0`, `SpSkillCustomizeParamViewModel.cs` `dcfccabe2edb8dd1bc1f0a05be81bdaefb9d517e`, and `XfbinParser.cs` `faf79d588fd8beb3f5761faebedd2252853b2f2b` are identical in both tag trees. The release-note feature delta is not evidence of a parser/ABI delta. |
| [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`, published 2026-08-30 | Also announces Switch Projectiles Target. |
| [NSC-Toolbox 2.1.2.0](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.0) | tag commit `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31`, published 2026-08-28 | Also announces Start Deflect / Stop Deflect. |
| Toolbox source comparison | 2.1.2.1 vs 2.1.2.0 | `SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`, `SkillEditorViewModel.cs` `870af492c41f26c2aab07c216b6fa5fd00ac2cbf`, `ConditionPrmModel.cs` `2827ca9e484eafb0c7435f066d42ff3e9345e17c`, and `XfbinParser.cs` `86c63708edf2698b5bc1c2a54c0480cce014b525` are identical across those tags. |
| [PyCriCodecs CPK reference](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111` | `PyCriCodecs/cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306` reads CPK header then UTF CPK metadata and follows TOC/ITOC/HTOC/GTOC/HGTOC offsets. `PyCriCodecs/utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb` parses @UTF/EUTF. Generic format reference only; it does not establish Switch archive precedence or native FileLoad lifetime. |
| [REA reverse-engineering methodology](https://github.com/morluto/rea/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4) | commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4` | README blob `474ecfbec32c2ef86e5d0cf17837892d5b07335a`; CLI/evidence guide blob `35f686aa26ba850b56e8a74df648f47d99a164e3`. The guide recommends retained Evidence and pinned static analysis in CI; methodology only, not a game-specific ABI source. |
| Pinned Switch v1.70 original main | Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes | SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`; Foundation workflow reads this exact tracked file and fails on mutation. |

## Current verified base evidence

The preceding branch HEAD `9975550ae11657970ae8905a808aa0360ad36710` passed the FileLoad guard-state test. Foundation artifact `15233949208` / ZIP SHA256 `53075cb3fbadba6548a2dc0080f429b3aedadb66d898164aebb971860deb04ff`; guard JSON SHA256 `c04f854b2be460035599ed07355ed9993183a5c0e544e828f0f9f7bf43e649bb`.

The pinned report records:
- Registration helper callsite `0x116b810 -> 0x290`.
- X0 is loaded from pointer cell `0x215d2b0`; X1 is the candidate static object `0x43717e0`; X2 is `0x1eb3000`.
- The pointer cell is in data at `0x215d2b0`, raw u64 is zero in the file image, and exactly one `DT_RELA` record exists at `0x1976d80`: `R_AARCH64_RELATIVE`, symbol index 0, addend decimal 18,266,248 = text offset `0x116b888`.
- The helper's bounded window contains atomic increment sites `0x2e0/0x2e8/0x2ec`, a 24-byte record stride from `0x2f8/0x2fc`, and stores X8/X1/X2 at `0x304/0x308`. Helper identity, table runtime target and destructor/callback semantics are not proven.
- The tracked original ExeFS tree contains the original main and a separate P128 reference main; no additional original Switch provider module is present in that tree.

## Implementation in this slice

New source: `tools/portlib/native_fileload_registration_target.py` (blob `8ee881958c72de9bc1fa14feea1a2806265ce952`)  
New test: `tests/test_native_fileload_registration_target.py` (blob `10b77976b8af26ef1c6720a30028c67cf7b96bd9`)  
Workflow change: `.github/workflows/verify-port-foundation.yml` (blob `c087b353eb4dbbe5512f49ba821fc92974a89db0`)

The analyzer reuses the SHA-pinned guard-state proof, requires exactly one `R_AARCH64_RELATIVE` relocation in cell `0x215d2b0`, checks the link-time text addend `0x116b888`, then disassembles a bounded `[0x116b888, 0x116b988)` window. It records reachable instruction words, register reads/writes, memory base/index/displacement/width/direction/writeback, direct calls as non-walked barriers, unresolved indirect calls/terminators, returns, out-of-window edges, raw aligned-text B/BL word candidates and the exact window SHA256. The window is explicitly not a function extent; the relative relocation addend is not treated as the runtime relocated pointer.

Synthetic regressions cover direct BL non-recursion, conditional branch/fallthrough, external branch exits, memory operand width/base, indirect BLR barriers, invalid alignment/entry, and reachability budget. The authentic-main test requires the original-main SHA, exact relocation slot/record/type/addend, executable-text target, nonempty bounded decode, and every callback/destructor/ABI/runtime release flag false.

## Falsifiable boundaries

This slice can falsify the relocation source, target offset, text bounds, instruction decode, CFG reachability, memory operand metadata, and direct/indirect control-flow inventory. It cannot by itself prove that the target is invoked as a callback, is a destructor, belongs to a complete function, owns or frees the static object, runs synchronously/asynchronously, participates in rollback/unbind, or supplies a consumer ABI. No runtime hook is added.

CI for the new code/test HEAD is pending. Inspect direct push API runs, raw job logs, and the Foundation artifact before promoting this note or status to VERIFIED.
