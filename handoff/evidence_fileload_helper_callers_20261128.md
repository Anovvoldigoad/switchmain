# FileLoad helper inbound caller census — implementation evidence

Date: 2026-11-28
Branch: `port/full-api-v170`
Implementation parent: `e70d151e7c7fffec838126f47d2f375e65e8ba34`
State before CI: IMPLEMENTED_AWAITING_CI

## Research-first primary sources

| Source | Exact ref | Inspected blob / result |
|---|---|---|
| [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`, published 2026-08-30 | Release note adds **Switch Projectiles Target**. `Model/SkillCustomizeParamModel.cs` `6a891e237d27fdf01336f806dbef8767d609a304`, `Model/SpSkillCustomizeParamModel.cs` `2b518f6eeb9ef97895517582e393a2adf9ee6da0`, and `XfbinParser.cs` `faf79d588fd8beb3f5761faebedd2252853b2f2b` are byte-identical to 2.1.2.0. |
| [NSC-ModManager 2.1.2.0](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0) | tag commit `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`, published 2026-08-28 | Release note adds **Start Deflect / Stop Deflect**. Tree comparison confirms the inspected parser/model blobs above are unchanged. |
| [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`, published 2026-08-30 | `Model/SkillEditorModel.cs` `e165471682e4a7aed91094ef07f92df271f31639`, `ViewModel/SkillEditorViewModel.cs` `870af492c41f26c2aab07c216b6fa5fd00ac2cbf`, `Model/ConditionPrmModel.cs` `2827ca9e484eafb0c7435f066d42ff3e9345e17c`, and `XfbinParser.cs` `86c63708edf2698b5bc1c2a54c0480cce014b525` are byte-identical to 2.1.2.0. `SkillEditorModel` contains projectile direction fields, but the inspected source does not define the Switch runtime ABI. |
| [NSC-Toolbox 2.1.2.0](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.0) | tag commit `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31`, published 2026-08-28 | Release note adds Start/Stop Deflect; inspected SkillEditor/XFBIN parser blob IDs match 2.1.2.1 exactly. |
| [UltimateStormAPI 2.1.2.1 source](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | commit `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, parent `1c3460573fa70b595e6bfa70e52f83f1c3f74f12` | `xinput9_1_0/MovesetPlus.cpp` blob `d7c5dbbebd60415f8d304321f083897658a86146` adds command 29 -> `TakeOverEnemyProjectiles`. The PC implementation uses a Windows mutex, `GetTickCount64`, a 250 ms stale-projectile window, and cached PC projectile pointers. Parent source has no `TakeOverEnemyProjectiles` implementation. This is Windows x64 behavior, not Switch ARM64 ABI evidence. |
| [PyCriCodecs CPK](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111` | `PyCriCodecs/cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306` parses CPK metadata and TOC/ITOC/HTOC/GTOC/HGTOC/ETOC chunks; `utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb` decodes @UTF/EUTF rows/columns. Format reference only; it does not establish Switch archive precedence. |
| [REA binary diagnostics](https://github.com/morluto/rea/blob/0386efd1e1dfa41af41f804a6be56c6f5b7615d4/docs/binary-diagnostics.md) | commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4`, doc blob `b58b8d04dc799813d0ebe0dcd4889560c707553c` | The pinned diagnostics profile explicitly returns unsupported for AArch64. It is therefore not used to decode this Switch main; Capstone 5.0.6 is pinned in the isolated workflow instead. |
| Pinned Switch v1.70 original main | branch tree blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes | Required SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`. GitHub Actions checks out and reads these exact tracked bytes; the previous table-census raw job log confirmed the hash-pinned original-main test passed. |

## Prior local evidence and CI

The current branch code parent is `e70d151e7c7fffec838126f47d2f375e65e8ba34`; the preceding code proof `0bc4cb45d713325cf8e33f0385b42535791fe5ab` passed run `46089004753`, job `140805260736`. The raw log was fetched directly and inspected; it emitted `PINNED_FILELOAD_REGISTRATION_LIFECYCLE_PASS` and `PINNED_FILELOAD_TABLE_ACCESS_CENSUS_PASS`. Artifact `15239987914`, ZIP SHA256 `97f2b7734baef912d6becf291ed88c2b2bc59427f641ca238b96cc29751bca28`, report SHA256 `49b68228ce6a598471d5778e9e847bdbb10c00e11bd7ae3e806618b923f7586d`.

The table census found 101 raw aligned direct B/BL inbound candidates to `0x116b390`, including `0x116b8a4` and `0x116b928`. The helper's previously verified bounded dispatch sequence loads X8 from [X0], loads X2 from [X8+0x58], copies X19 to X1, then executes BR X2 at `0x116b3d0`. The target remains unresolved.

Earlier failed table-census attempts were checked from raw logs:
- Run `46088082330` / job `140802291968`: synthetic ADRP page encoder treated page delta as bytes.
- Run `46088241951` / job `140802797820`: authentic first-slot read failed because the analyzer omitted MOV X19,XZR plus ADD X8,X20,X19 reaching values. The fixed analyzer added bounded known-value propagation; this is not repeated here.

## New vertical slice

New source: `tools/portlib/native_fileload_helper_callers.py`  
New regression: `tests/test_native_fileload_helper_callers.py`  
Isolated workflow: `.github/workflows/verify-fileload-helper-callers.yml`

The analyzer:
1. Reproduces the raw aligned B/BL scan for target `0x116b390`.
2. Requires Capstone to confirm each branch instruction and target before classifying it.
3. Captures a fixed `0x40`-byte prelude for each confirmed branch, including little-endian instruction words, read/write register sets, memory base/index/displacement/width, and control-flow barriers.
4. Records the last syntactic write to architectural X0-X7 in that prelude and groups callers by a deterministic signature hash. The report explicitly labels these as syntactic writes, not reaching definitions or ABI arguments.
5. Reproduces the two known table-path callsites: `0x116b8a4` and `0x116b928`, each preceded by `LDR X0,[X8,#0x28]` at `0x116b8a0` and `0x116b924`.

## Falsifiable boundaries

- The raw inbound count is expected to remain 101 on the pinned main; any change fails the regression.
- Both table-path calls must remain direct BLs to `0x116b390`.
- Each known call must retain the exact 64-bit X8+0x28 load as the last syntactic X0 write in the bounded prelude.
- Every signature cluster must account for exactly the Capstone-confirmed rows; unconfirmed raw words are preserved separately, never silently discarded.
- No function extent, parameter meaning, C++ class, producer, table writer, BR X2 target, callback/vtable/destructor, ownership, lock/unlock, async, rollback/unbind, native consumer ABI, archive precedence, emulated ARM64, or Uzuy behavior is inferred.

## Status

The new implementation is awaiting its isolated direct-push GitHub Actions run. Do not promote this note to verified until the exact commit's job is COMPLETED SUCCESS, the original raw log is inspected, and the JSON artifact is verified.
