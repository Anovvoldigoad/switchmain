# FileLoad status-service target implementation evidence — 2026-11-27

## Research-first source pins

- **NSC-ModManager latest release:** [2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), published 2026-08-30, release ID 379313827; tag commit 502c38d3ee832509f9ee3951b7d3339826538fec. Its release body says Switch Projectiles Target changes the owner of enemy projectiles. Prior 2.1.2.0 tag commit: a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983; its notes advertise Start Deflect / Stop Deflect.
- The repository's ModManager source pin 276116ebf5ba398a867793cb02ee6c33c0927645 is a direct child of the 2.1.2.1 tag, not a pre-2.1.2.1 source. Relevant model blob Model/SkillCustomizeParamModel.cs is 6a891e237d27fdf01336f806dbef8767d609a304 at both release tags. The pinned SkillCustomizeParamViewModel.cs blob is ced6d805b207fae16cf68df87e23744608d6562b.
- **NSC-Toolbox latest release:** [2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1), published 2026-08-30, release ID 379314127; tag commit 789fe96f99cdaa77f952b90b563c6e3f49b6d697. Prior 2.1.2.0 tag commit: dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31. ViewModel/SkillEditorViewModel.cs blob 870af492c41f26c2aab07c216b6fa5fd00ac2cbf is byte-identical at both tags; Model/SkillEditorModel.cs blob e165471682e4a7aed91094ef07f92df271f31639 is also the pinned parser/model source. Therefore the release note does not provide a new numeric Event236 ID or Switch consumer ABI.
- **CRI format reference:** [PyCriCodecs](https://github.com/t-wy/PyCriCodecs), pinned commit 755055ee7b056c9c1aefc6505a3daa3e45e2e111; cpk.py blob 2ed2cbb2c6112124013ab52755dba8a443e91306, utf.py blob d1662d140a48cae37a6696213ee441aed4076edb. It documents CPK TOC and @UTF table parsing; it does not establish Storm Connections Switch runtime ownership or precedence.
- **Independent RE methodology:** [REA](https://github.com/Black-Star-Pen/REA), pinned commit 0386efd1e1dfa41af41f804a6be56c6f5b7615d4; README blob 474ecfbec32c2ef86e5d0cf17837892d5b07335a, CLI/evidence guide blob 35f686aa26ba850b56e8a74df648f47d99a164e3. REA is a general reverse-engineering workflow, not a CRI CPK implementation.

## Prior exact-main service-entry evidence

- Pinned Switch v1.70 original main Git blob: 8af900db0d7003255b4ddb3cbd1289cd5a15458e; required SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9.
- Previous code commit: c89d815a2a8e6004ff14d4dd7d950e9d95bfc35e, parent 0e84462e75faa2912bca6a5698987d38d23920eb.
- Foundation push run 46013548161, job 140554824874, completed success. Raw log inspected. Artifact 15205855931, ZIP digest a9c1629821af7fdc6cf3826657ce2eaacc39b237f17576c6386e973eeee465e.
- Exact 128-byte window 0x1215358..0x12153d8, SHA256 57ceb7351df052e968a1431e70c39812c323d0880d00d36380c01814af58976e.
- 0x1215358 and 0x1215374 both begin ldr w8, [x0, #0x28]. Their nonzero branches adjust X0 by +8, then direct-branch to 0x1158c90 and 0x1158d10. A separate helper at 0x1215390 checks [x0+0x28] == 1, calls 0x1158d30 with X0+8, then clears [x19+0x28].
- These are concrete direct dispatch targets and object-relative accesses. They are not proof that the targets are mutex lock/unlock routines. The previous Unicorn status-slice models these services as no-op and therefore cannot supply their semantics.

## New falsifiable slice

- Disassemble the exact-main 256-byte window 0x1158c90..0x1158d90 and capture every word, register read/write, memory base/index/displacement/writeback and direct B/BL edge.
- Run a bounded direct-control-flow trace rooted independently at 0x1158c90, 0x1158d10, and 0x1158d30. Direct calls are recorded but not recursively followed; indirect calls/branches and out-of-window edges remain explicit unresolved boundaries. Fixed windows are not treated as function extents.
- Scan the entire pinned text for direct B/BL incoming edges to all three targets and require the service-window callers:
  - 0x1215364 B 0x1158c90
  - 0x1215380 B 0x1158d10
  - 0x12153a8 BL 0x1158d30
- Synthetic regressions cover unconditional/conditional branches, direct BL (callee not recursively followed), indirect BR, out-of-window targets, instruction-budget exhaustion, and invalid aligned-window boundaries.
- **Falsifiable hypothesis:** the target trio may implement paired synchronization or reference-state services on the X0+8 subobject. Accept a lock/unlock interpretation only if target instructions plus call/import evidence demonstrate matching acquire/release behavior. A plain field test, branch, indirect call, or status-byte clear is insufficient.
- No runtime hook, object write, ABI assumption, or release flag change is authorized by this evidence.

## Execution boundary

Implementation parent: c89d815a2a8e6004ff14d4dd7d950e9d95bfc35e. New target-body evidence is PENDING_CI until the Foundation push run's raw job log and machine-readable artifact are inspected.


## CI attempt 1 correction

Foundation push run 46017177259/job 140567169891 failed in the synthetic test only: the test incorrectly treated the aligned, in-bounds range [0,12) of a 16-byte fixture as invalid. The raw job log was inspected. The test now asserts this is a valid shorter window with an out-of-window fallthrough edge and uses end=20 for the invalid boundary. Production analyzer logic was not implicated. Retry CI is required.
