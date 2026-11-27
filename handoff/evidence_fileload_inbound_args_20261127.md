# FileLoad single-caller argument provenance — 2026-11-27

## Parent and scope

- Repository: https://github.com/Anovvoldigoad/switchmain
- Branch: \`port/full-api-v170\`
- Parent HEAD: \`28e514ffc075dec65b764d7a66b311317d35fc0a\`
- Game input: Switch v1.70 original \`main\`, SHA256 \`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9\`
- Existing authentic Foundation artifact: [run 46036147360 / artifact 15219430039](https://github.com/Anovvoldigoad/switchmain/actions/runs/46036147360)
- Existing artifact evidence: the corrected FileLoad entry is \`0x116f404\`; one direct incoming BL was found at \`0x116f29c\`. Inside the entry, \`mov x20, x2\` at \`0x116f434\` and \`mov x22, x1\` at \`0x116f438\` copy incoming argument-register values. Their pointer identity, type, ownership and lifetime remain unproven.

## Primary-source research

- Latest [NSC-ModManager 2.1.2.1 release](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), published 2026-08-30. Release notes add “Switch Projectiles Target” and an ASBR camera fix. The repository pin \`276116ebf5ba398a867793cb02ee6c33c0927645\` is the 2.1.2.1 release commit.
- ModManager source blobs at tag 2.1.2.1:
  - \`Model/SkillCustomizeParamModel.cs\`: \`6a891e237d27fdf01336f806dbef8767d609a304\`
  - \`ViewModel/SkillCustomizeParamViewModel.cs\`: \`ced6d805b207fae16cf68df87e23744608d6562b\`
  - \`ViewModel/TitleViewModel.cs\`: \`f7ca7602d12cf9689a08fd6b7e55abc4dc8fd4ca\`
  - The first two blobs are identical at 2.1.2.0 and 2.1.2.1. The TitleViewModel blob changed, but its source text does not contain the literal “projectile”; the release note alone is not evidence of a Switch runtime consumer.
- Latest [NSC-Toolbox 2.1.2.1 release](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1), published 2026-08-30. Parser/editor blobs at 2.1.2.1:
  - \`Model/SkillEditorModel.cs\`: \`e165471682e4a7aed91094ef07f92df271f31639\`
  - \`ViewModel/SkillEditorViewModel.cs\`: \`870af492c41f26c2aab07c216b6fa5fd00ac2cbf\`
  - Both are identical at 2.1.2.0 and 2.1.2.1; no parser-layout change is evidenced by these files.
- Independent CRI references:
  - [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111), commit \`755055ee7b056c9c1aefc6505a3daa3e45e2e111\`; \`cpk.py\` blob \`2ed2cbb2c6112124013ab52755dba8a443e91306\`, \`utf.py\` blob \`d1662d140a48cae37a6696213ee441aed4076edb\`.
  - [REA](https://github.com/Black-Star-Pen/REA/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4), commit \`0386efd1e1dfa41af41f804a6be56c6f5b7615d4\`; README blob \`474ecfbec32c2ef86e5d0cf17837892d5b07335a\`.
- Game-specific byte source is the SHA-pinned original Switch v1.70 \`main\`; the analyzer rejects any other SHA before reading the callsite.

## New falsifiable analysis

The direct incoming caller at \`0x116f29c\` is now the sink for a bounded argument-origin analysis:

- Window: \`[0x116f09c, 0x116f2a0)\`, exactly 0x204 bytes.
- This is deliberately **not** asserted to be a function extent.
- The analyzer scans direct B/BL edges into the window; external entries become unknown roots.
- It builds a bounded CFG, unions reaching definitions at merges, and treats every earlier BL/BLR/SVC as an X1/X2 clobber barrier. No AAPCS or cross-OS engine ABI is assumed.
- Definitions retain exact instruction word, register reads/writes, and memory base/index/displacement. Stack-relative ADD and memory-loaded arguments remain distinguishable.
- Synthetic tests cover exact register copies, call barriers, conditional merge, SP-relative address formation, memory-load origin, unknown window entry, and invalid window bounds.
- The original-main integration test requires exactly one direct BL to the corrected FileLoad entry and SHA256 identity.

## Hypothesis and acceptance boundary

Hypothesis: the caller-side X1/X2 values are derived from concrete stack, memory, or register definitions that can be followed further toward object construction/borrowing. The report can falsify this by returning only window-entry or call-barrier origins, or multiple conflicting definitions.

Even a unique reaching definition does **not** prove pointer type, allocation, ownership, destructor, async completion, rollback, unbind, archive precedence, native consumer ABI, or runtime compatibility. Those flags remain false. No hook or game write is introduced.

## CI state at creation

PENDING_CI for the new code. No PASS is claimed until the push-triggered Foundation, compressed PRM, factory and MovesetPlus runs for the new HEAD complete and their raw job logs are inspected.
