# FileLoad X19 recursive stack-proof tree — 2026-11-28

## Research-first source pins

- Latest [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), published 2026-08-30, tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`. Its release note adds **Switch Projectiles Target**.
- Previous [NSC-ModManager 2.1.2.0](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.0), published 2026-08-28, tag commit `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`. Its release note adds **Start Deflect / Stop Deflect**.
- Repo-pinned PC ModManager source commit: `276116ebf5ba398a867793cb02ee6c33c0927645`. Compared against 2.1.2.1: these four relevant blobs are identical at the pinned and latest commits: `Model/SkillCustomizeParamModel.cs` `6a891e237d27fdf01336f806dbef8767d609a304`; `ViewModel/SkillCustomizeParamViewModel.cs` `ced6d805b207fae16cf68df87e23744608d6562b`; `Model/SpSkillCustomizeParamModel.cs` `2b518f6eeb9ef97895517582e393a2adf9ee6da0`; `ViewModel/SpSkillCustomizeParamViewModel.cs` `dcfccabe2edb8dd1bc1f0a05be81bdaefb9d517e`. The release-level feature additions therefore do not imply changes to these inspected parser/editor sources, and do not establish a Switch engine ABI.
- Latest [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1), tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697); prior 2.1.2.0 tag commit `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31`. The inspected `Model/SkillEditorModel.cs` blob `e165471682e4a7aed91094ef07f92df271f31639` is identical across these tags.
- [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) pinned at `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; inspected CPK/UTF parser blobs `2ed2cbb2` and `d1662d14`. This is a CRI format reference, not a game-specific runtime proof.
- [REA](https://github.com/Black-Star-Pen/REA/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4) pinned at `0386efd1e1dfa41af41f804a6be56c6f5b7615d4`; inspected README blob `474ecfbe` and CLI reference blob `35f686aa`. Methodology only.
- Game-specific input: `original/atmosphere/contents/0100FA10190A0000/exefs/main`, Git blob `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes. Required SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`; the successful Foundation job revalidated this through the pinned original-main tests.
- Local prior evidence: `evidence_fileload_caller_x19_20261128.md` and `evidence_fileload_x19_stack_restore_20261128.md`. The current source changed from blob `bc78752ebb7d8e6dd8d8f890d622ebfae6d8ec1c` to `3bbc79d69029ac58138844d12b57592a95ae79d1`; the regression file remains blob `6af075cdaf5f30dec3aed2c3d8556f473d86d2c6`.

## Failure on prior HEAD and correction

Prior HEAD `255adab51824809ca8920c4b65dba6a3d326fb41` had a Foundation failure at run/job `46065381856/140729313554`, step 42. The raw log showed the recursive serializer calling `.values()` on `child["nested_call_proofs"]`. The child analyzer returns that field as a list on both normal and fail-closed paths, so the serializer raised `AttributeError: 'list' object has no attribute 'values'`. The other three workflows on that prior HEAD succeeded; their raw logs were inspected.

Code commit: `dbc23b155335c61602437c72e7f1ceabbe35553d`, parent `255adab51824809ca8920c4b65dba6a3d326fb41`.

Surgical fix in `tools/portlib/native_fileload_call_targets.py`:
- before: `list(child["nested_call_proofs"].values())`
- after: `list(child["nested_call_proofs"])`

No hook, ABI assumption, stack-barrier relaxation, or workflow change was made. Existing regressions in `tests/test_native_fileload_inbound_args.py` exercise empty child lists, recursive call-graph cycles, and nested proof-list shape. The existing Foundation workflow already runs this test at step 42.

## CI for code/test HEAD

All four push workflows for `dbc23b155335c61602437c72e7f1ceabbe35553d` completed SUCCESS; raw job logs were read:

| Workflow | Run / job |
|---|---|
| Foundation | `46066250617 / 140732155719` |
| Factory | `46066250621 / 140732155517` |
| Compressed PRM | `46066250642 / 140732155515` |
| MovesetPlus | `46066250702 / 140732155859` |

Foundation artifact `PORT_FOUNDATION_PROOFS_NOT_A_GAMEPLAY_RELEASE`, artifact ID `15231780092`, 336,355 bytes, SHA256 `598559d70ee9d2911c52fc6109b722465b87b96d3e5b9b77f2de8b99f38fc7aa`.

- `native_fileload_inbound_args.json`: 617,011 bytes, SHA256 `d3a1ece8b05743da15643babe98d77fffa0995532477f0bf6e769bbec66102e5`.
- `native_fileload_call_targets.json`: SHA256 `ff165a8a94f42d19b9e70d9e9642250afcb76ccdba2f876cf1da77490413394d`.

Authentic log markers include `PINNED_FILELOAD_INBOUND_ARGUMENTS_PASS`, `PINNED_FILELOAD_SERVICE_WRAPPERS_EMULATED_PASS`, and `RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS`. The emulated ARM64 service slice is explicitly not a Uzuy test.

## Original-main result: exact local save/restore, unresolved nested effects

At FileLoad caller `0x116f280 -> 0x120a6c8`:
- Bounded target window: `[0x120a6c8, 0x120a8c8)`, SHA256 `60189963ab42120388f1b88d443ad722ae48275830ea07d2edd415140ee54f12`.
- Exact incoming-X19 save: `0x120a6c8: stp x30,x19,[sp,#-0x10]!`, X19 slot at entry-SP `-0x8`.
- Exact restore: `0x120a724: ldp x30,x19,[sp],#0x10`, same entry-SP `-0x8` slot.
- Observed return: `0x120a728`.
- `all_return_paths_restore_entry_register=true`; `sp_balanced_on_all_returns=true`; but `sp_delta_trusted_on_all_returns=false`, so `preservation_proven=false` with reason `NESTED_CALL_STACK_EFFECT_UNPROVEN`.

The recursive proof tree now serializes and identifies the remaining blockers:

| Nested callsite | Target | Result | Concrete unresolved evidence |
|---|---:|---|---|
| `0x120a6d0` | `0x116b698` | `NESTED_CALL_STACK_EFFECT_UNPROVEN` | One unknown X19-based store; child `0x116b6c0 -> 0x116b7b0` also fails, with two no-return bounded targets `0x12f3690`/`0x12f36a0` and an unknown-store target `0x290` |
| `0x120a6e8` | `0x1188104` | `UNKNOWN_MEMORY_ALIAS_STORE` | Five unknown stores through X0 |
| `0x120a6f0` | `0x1170f7c` | `NESTED_CALL_STACK_EFFECT_UNPROVEN` | Three unknown X19-based stores; child `0x1170f84 -> 0x11704c4` has six unknown X0 stores |
| `0x120a6f8` | `0x1160c64` | `UNKNOWN_MEMORY_ALIAS_STORE` | Three unknown stores through X0 |

The parent target also reports eight X19-based memory writes after the first nested call, because pointer provenance is not retained across the unproven nested effects. The proof tree does **not** establish that these writes are disjoint from the saved slot. Consequently X19 remains a call barrier at `0x116f280`; the caller's X2 copy at `0x116f294` remains unresolved. This is a real improvement in evidence output, not proof of a consumer pointer.

## Explicit limits and next work

- No native consumer ABI, object type, ownership/lifetime, callback, lock/unlock implementation, async completion, rollback, unbind/destructor, archive precedence, or Uzuy gameplay proof.
- No runtime hook was added. `full_moddingapi=false`, `ready_for_gameplay_test=false`, `emulator_tested=false`.
- Preserve Sakura aura107 and both Event236 forms: marker `0x4E53 + 0x2A` and no-marker Event236.

Next: continue from `0x116b698` and nested `0x116b6c0 -> 0x116b7b0`. Prove exact X1/X19 pointer provenance and each unknown store against the protected entry-SP `-0x8` slot. Investigate `0x12f3690` and `0x12f36a0` bounded control-flow exits without assuming function extents. Keep the original FileLoad caller barrier until all nested stack and alias conditions are proven.
