# FileLoad 0x116b82c return-value provenance — evidence note

Date: 2026-11-28  
Branch: `port/full-api-v170`  
Parent before implementation: `827ec3897c1559f65fbeef25eb4712a5d04c3faa`  
State at code commit: PENDING_CI

## Research-first primary sources consulted in this execution

| Source | Exact ref / revision | Retrieved source identity |
|---|---|---|
| [NSC-ModManager release 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`; latest main commit `276116ebf5ba398a867793cb02ee6c33c0927645` | `XfbinParser.cs` blob `faf79d588fd8beb3f5761faebedd2252853b2f2b`; release note published 2026-08-30. The release adds Switch Projectiles Target. |
| [NSC-Toolbox release 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; latest main commit `6f780cb6814f07e03c16b3e78d97dde4e4368983` | `Model/SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639`; `XfbinParser.cs` blob `86c63708edf2698b5bc1c2a54c0480cce014b525`. Editor exposes projectile direction fields; it does not define Switch runtime ABI. |
| [UltimateStormAPI](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | pin `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`, parent `1c3460573fa70b595e6bfa70e52f83f1c3f74f12` | `xinput9_1_0/MovesetPlus.cpp` blobs `d7c5dbbebd60415f8d304321f083897658a86146` and `e96af51210e96926a7bdaa70c44b6645f1a2b2b6`. Cases 27/28 and `SetProjectileDeflection` exist in both; case 29 / `TakeOverEnemyProjectiles` only in the newer pin. The method uses a Windows mutex and `GetTickCount64` with a 250 ms freshness window; do not treat it as Switch ABI. |
| [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111` | `cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`; `utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`. Independent CRI CPK/@UTF format reference only. |
| [REA binary diagnostics](https://github.com/morluto/rea/blob/0386efd1e1dfa41af41f804a6be56c6f5b7615d4/docs/binary-diagnostics.md) | commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4` | doc blob `b58b8d04dc799813d0ebe0dcd4889560c707553c`; inspected profile explicitly marks AArch64 unsupported, so it is not used to decode Switch code. |
| Pinned Switch v1.70 original main | branch blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes | Required SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`; GitHub Actions rehashes this exact tracked file. |

## Byte-level target and falsifiable hypothesis

- Existing dispatch evidence pins caller BL at `0x116b3b0 -> 0x116b82c`.
- Immediately before that call, caller X0 is sourced from X20; X20 was loaded from the post-call X0 at `0x116b7b0`. X1 comes from W0 after the call at `0x116d380`.
- After the call, caller code checks X0 at `0x116b3b8`, loads X8 from `[X0]` at `0x116b3bc`, loads X2 from `[X8,#0x58]` at `0x116b3c4`, then branches through X2 at `0x116b3d0`.
- The target's bounded `0x100`-byte CFG is expected to contain return sites `0x116b858` and `0x116b870`, and a direct diagnostic call at `0x116b864 -> 0x12155a0`.
- Falsifiable hypothesis: every reachable return from `0x116b82c` can be classified as an entry-register copy, a symbolic memory-derived value, a constant, or unknown after an untraced call. This does not assign a C++ type or semantic meaning to the value.

## Implementation

- New analyzer: `tools/portlib/fileload_return_provenance.py`.
- New regressions: `tests/test_fileload_return_provenance.py`.
- The analyzer walks only the already-bounded CFG; direct/indirect call targets are not followed. All GPR/SP provenance is invalidated after an untraced call. Memory reads remain symbolic. Unsupported register writes become unknown.
- Positive/negative/boundary synthetic cases cover register copy, symbolic load, call-clobber barrier, post-call constant redefinition, conditional path divergence, invalid CFG metadata, and mutated original-main rejection.
- No function identity, native ABI, callback, object type, ownership, lock/unlock, async, rollback/unbind/destructor, archive precedence, runtime hook, ARM64 emulation, Uzuy or gameplay result is asserted.

## CI

Awaiting targeted push workflow on the exact code commit. Do not promote this slice to verified until the job is COMPLETED SUCCESS and its raw log is inspected.


## Reproduced result and CI (2026-11-28)

Code commit: `e9555de6024a334b6ffcac1e7b9c091fee79d7e6`; parent: `9fafb58369cd61a3bf691a99c1b134912787fedd`.

### Table scan result
- Raw workflow log: run `46109004389`, job `140868100989`, COMPLETED SUCCESS.
- Artifact: `FILELOAD_TABLE_ACCESS_STATIC_EVIDENCE`, ID `15248364167`, zip SHA256 `d1757312874c72ca2ef83300573a0258ff666bcc0a92069ef5e64de95c3aa77a`.
- Report JSON: 261,617 bytes, SHA256 `538dd282ac1f7af783d54b125d31958f0092b591d7be61032b261cd6d67ab7be`.
- Result: 89 ADRP page references, 34 direct accesses (2 reads, 32 writes), 7 symbolic indexed reads, 0 indexed writes, 0 direct writes outside the two bounded 512-byte zeroing sequences.
- Seven indexed read sites: `0x116b844`, `0x116b9b0`, `0x116ba2c`, `0x116baf4`, `0x116bbc0`, `0x116bc88`, `0x116bd54`. Each uses `0x4371800 + UXTW(W1)*8`, loads 8 bytes, and remains unresolved for the runtime index value.

### Return-provenance result
- Raw workflow log: run `46109004391`, job `140868101178`, COMPLETED SUCCESS.
- Artifact: `FILELOAD_RETURN_PROVENANCE_STATIC_EVIDENCE`, ID `15248891039`, zip SHA256 `e269519033e4ee250c2120357632952a25d0e1d92aea60f8459ed369ec962706`.
- Report JSON: 17,578 bytes, SHA256 `53ebe0d7eff1ffbdcb45fc838d63148b587fe76f0b0992d6baa2475f2ffba337`.
- Exact lookup: `CMP W1,#0x3f; B.HI` bounds the index to 0..63; `ADRP X8,0x4371000`; `ADD X8,X8,#0x7d8`; `ADD X8,X8,W1,UXTW #3`; `LDR X0,[X8,#0x28]`. Effective base is `0x4371800`.
- The loaded value is compared to `0x3f800000`. Out-of-range or equal-sentinel paths reach `RET` at `0x116b870` with X0=0. The non-sentinel path returns the loaded 64-bit slot value at `0x116b858`.
- Caller `0x116b3b0` then null-checks X0, dereferences `[X0]`, loads `[X8,#0x58]`, and branches via X2. No object type or vtable target is inferred.

### Failure/correction history
- Run `46108343732` failed because the first analyzer omitted the `hashlib` import; corrected in commit `386cee9adc9195dce5b2efee4c4b4703a1b9f884`.
- Run `46108507058` failed because a test treated Capstone's reported CMP X0 write as a real GPR write. The pinned disassembly shows `CMP X0,X8` only updates NZCV. The analyzer now treats compare aliases as flag-only; final runs above pass.

### Scope boundary
All findings are static host analysis of the SHA-pinned original main plus synthetic tests. Calls are not followed; memory values are symbolic. The 89-ADRP writer scan is bounded-linear and does not prove absence of branch-path or memory-loaded pointer aliases. Native ABI, producer lifecycle, callbacks, ownership, archive precedence, ARM64 emulation, Uzuy and gameplay remain unverified.
