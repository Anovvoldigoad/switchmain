# FileLoad X19 stack-slot dataflow — 2026-11-28

## Research-first source pins and comparison

- NSC-ModManager release 2.1.2.1: https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1, tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`; prior 2.1.2.0 tag `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`. Release 2.1.2.1 notes Switch Projectiles Target; the 2.1.2.0 patchnotes blob `37c3d8b0bc6e8b0f334edc215b5d414177fada4c` records Start Deflect and Stop Deflect. The tag comparison is one commit; relevant source/UI/config/patchnote changes do not alter the Toolbox SkillEditor model blob below. No Switch runtime ABI or numeric event ID is inferred.
- NSC-Toolbox 2.1.2.1 tag `789fe96f99cdaa77f952b90b563c6e3f49b6d697`; prior 2.1.2.0 tag `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31`. `Model/SkillEditorModel.cs` is the same Git blob at both tags: `e165471682e4a7aed91094ef07f92df271f31639`. This is a PC editor/parser source comparison only.
- CRI CPK/@UTF format reference: PyCriCodecs main commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`; `PyCriCodecs/cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`, `PyCriCodecs/utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`. Format reference only.
- Independent reverse-engineering workflow reference: REA main commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4`; README blob `474ecfbec32c2ef86e5d0cf17837892d5b07335a`, CLI guide blob `35f686aa26ba850b56e8a74df648f47d99a164e3`. Generic methodology only, not Switch ABI evidence.

## Pinned game bytes and prior verified evidence

- Repository: https://github.com/Anovvoldigoad/switchmain
- Branch: `port/full-api-v170`
- Parent HEAD: `ace04f5ea7a8a21b9a625eb69fdce3d95eb767e6`
- Original Switch v1.70 main path: `original/atmosphere/contents/0100FA10190A0000/exefs/main`
- Git blob: `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes.
- Required whole-file SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- Prior code/test HEAD `ac71215f23bd645119f830cc4c63d0b5b2f1974b` passed all four push workflows; prior final documentation HEAD `ace04f5ea7a8a21b9a625eb69fdce3d95eb767e6` also passed all four push workflows. The direct Actions API showed no active runs on this branch. The four parent run/job pairs were Foundation `46049562497/140677207099`, factory `46049562404/140677206386`, compressed candidate `46049562431/140677206505`, MovesetPlus `46049562409/140677206864`; raw job logs were read. Foundation artifact `15224036889`, ZIP SHA256 `2faea0bc25db8b784796e4309c97cecaff65b694e1f084eed78dae952619522f`.
- The prior caller analysis has 23 raw-word direct BLs in `[0x116f09c,0x116f2a0)`; FileLoad callsite `0x116f29c` targets `0x116f404`. X19 is still a call barrier at `0x116f280 -> 0x120a6c8`; the bounded target report records X19 writes at `0x120a6cc: mov x19,x0` and `0x120a724: ldp x30,x19,[sp],#0x10`, four nested direct calls, and one bounded return at `0x120a728`. Previous code did not calculate exact stack-slot provenance.

## Implemented vertical slice

- Added `analyze_stack_register_restore` to `tools/portlib/native_fileload_call_targets.py`.
- The analyzer propagates path-sensitive SP delta, SP trust, tracked-register origin, and exact 8-byte stack-slot contents through the bounded CFG.
- It recognizes exact X-register `STR/STP` and `LDR/LDP` transfers, pre-index and post-index SP updates, and checks every observed return path.
- It refuses preservation if a nested call has unproven stack effects, a non-SP store may alias a live saved slot, an indexed stack access is unresolved, SP is unbalanced/untrusted, or control flow leaves/escapes the bounded window.
- `prove_register_preservation` now uses this proof only as a fallback for X19-writing callees. Other tracked-register proof behavior is unchanged.
- Synthetic regressions cover exact save/restore, wrong destination, overwritten slot, nested-call barrier, unknown-base store, conditional untouched return, conditional clobber, unbalanced SP, and invalid window bounds.
- The existing Foundation workflow already runs `tests/test_native_fileload_inbound_args.py`; no workflow YAML change is required.

## Evidence boundary

The new analyzer is a read-only static proof over the SHA-pinned original main plus synthetic instruction fixtures. The synthetic positive proves the algorithm can recognize an exact stack roundtrip; it is not evidence that the Switch callee preserves X19. The original-main assertion keeps `0x120a6c8` as a barrier unless the new artifact proves every required condition. A local restore observation under an untrusted post-call SP delta is explicitly not preservation.

No pointer type, object identity, allocation, ownership/lifetime, destructor, callback, async completion, rollback, unbind, imported runtime provider, archive precedence, nine-parser native consumer ABI, or Uzuy gameplay is established. No hook or game byte is changed. Sakura aura107 and both Event236 variants are untouched. All three release flags remain false.

Initial state for this commit: PENDING_CI. Inspect the Foundation raw job log and artifact, plus all other push workflow logs, before updating status to CI-verified.
