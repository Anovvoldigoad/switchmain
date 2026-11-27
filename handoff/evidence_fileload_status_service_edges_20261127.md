# FileLoad status-service entrypoint evidence — 2026-11-27

## Research-first source pins

### NSC-ModManager

- Latest release: [2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), published 2026-08-30; tag commit `502c38d3ee832509f9ee3951b7d3339826538fec`.
- Prior release tag 2.1.2.0: commit `a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983`.
- The project pin `276116ebf5ba398a867793cb02ee6c33c0927645` is a direct child of the 2.1.2.1 tag commit, not an older pre-2.1.2.1 source. Its commit message is `2.1.2.1 update`; the visible diff updates the packaged ModdingAPI binary/config and version metadata.
- Relevant parser/model blobs are unchanged across 2.1.2.0 and 2.1.2.1:
  - `Model/SkillCustomizeParamModel.cs`: blob `6a891e237d27fdf01336f806dbef8767d609a304`.
  - `ViewModel/SkillCustomizeParamViewModel.cs`: blob `ced6d805b207fae16cf68df87e23744608d6562b`.
- `ViewModel/TitleViewModel.cs` at 2.1.2.1 is blob `f7ca7602d12cf9689a08fd6b7e55abc4dc8fd4ca`; its relevant change is character-select page-count patching, not the new projectile-target event parser.
- The 2.1.2.1 release body advertises **Switch Projectiles Target**. The 2.1.2.0 bundled patch notes blob `37c3d8b0bc6e8b0f334edc215b5d414177fada4c` lists **Start Deflect** and **Stop Deflect**. These are PC release facts, not Switch engine ABI or numeric Event236 evidence.

### NSC-Toolbox

- Latest release: [2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1), tag commit `789fe96f99cdaa77f952b90b563c6e3f49b6d697`.
- Prior 2.1.2.0 tag commit: `dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31`.
- The relevant parser/editor source blobs are unchanged across those tags:
  - `ViewModel/SkillEditorViewModel.cs`: `870af492c41f26c2aab07c216b6fa5fd00ac2cbf`.
  - `Model/SkillEditorModel.cs`: `e165471682e4a7aed91094ef07f92df271f31639`.
  - `Properties/Program.cs`: `9d5f3e0dfa4ed51cf7924b503081a87b12146f64`.
- The 2.1.2.1 compare changes costume-entry mapping/localization and bundled runtime/config files; the SkillEditorViewModel parser/editor blob is identical. Its existing projectile lists do not name a new Switch Projectiles Target event. Therefore neither the new Event236 numeric value nor a Switch consumer ABI can be inferred from these parser/editor sources.

### Independent binary-format and RE references

- [PyCriCodecs](https://github.com/t-wy/PyCriCodecs), pinned commit `755055ee7b056c9c1aefc6505a3daa3e45e2e111`:
  - `PyCriCodecs/cpk.py` blob `2ed2cbb2c6112124013ab52755dba8a443e91306`.
  - `PyCriCodecs/utf.py` blob `d1662d140a48cae37a6696213ee441aed4076edb`.
  - `PyCriCodecs/chunk.py` blob `aab0cf82b7ce599811762bda3a089cb0f8aa41b4`.
  - These document CPK header/TOC/ITOC and @UTF table handling; they do not establish Storm Connections Switch consumer ABI.
- [REA](https://github.com/Black-Star-Pen/REA), pinned commit `0386efd1e1dfa41af41f804a6be56c6f5b7615d4`:
  - README blob `474ecfbec32c2ef86e5d0cf17837892d5b07335a`.
  - `docs/cli.md` blob `35f686aa26ba850b56e8a74df648f47d99a164e3`.
  - REA is a generic reverse-engineering workflow/evidence tool, not a CRI CPK parser and not evidence of Switch runtime semantics.

## Pinned Switch 1.70 bytes and local evidence

- Original main path: `original/atmosphere/contents/0100FA10190A0000/exefs/main`.
- Git blob: `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, 27,701,509 bytes.
- Required whole-file SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- Existing exact-main FileLoad status helper window: `0x120661c..0x12066bc` (160 bytes), SHA256 `fa5826cdfc6d88ea3e974578e266caad79e83b604eae441fd12840bba27b9bfa`.
- The helper receives object pointer X0 and requested status W1. At `0x1206624` it computes X19 = X0 + 0x18; at `0x1206628` it preserves X0 in X21; at `0x1206630` it preserves W1 in W20. It calls `0x1215358` at `0x1206634`, reads `[X21 + 0x68]`, preserves old values 3 or 5, otherwise writes W20 to `[X21 + 0x68]`, and transfers to `0x1215374` on the observed exit paths.
- The same direct-target pair also appears in the FileLoad request corridor rooted at `0x1206b4c`: `0x1206bf4 BL 0x1215358` and `0x1206c44 BL 0x1215374`.
- The two target addresses are therefore reproducible **direct call/branch candidates shared by two FileLoad-related code corridors**. Calling them “lock” and “unlock” remains a hypothesis: the existing Unicorn status-slice test stubs both addresses as no-op services and does not execute their real implementations.

## New falsifiable evidence slice

- Add a 128-byte exact-main disassembly window `0x1215358..0x12153d8`, explicitly not a function boundary.
- Record every 4-byte instruction, exact word bytes, direct B/BL target, register reads/writes and memory base/index/displacement/writeback.
- Extend the whole-text direct branch census with anchors `0x1215358` and `0x1215374`; require the six known incoming direct edges from the status helper and FileLoad request corridor.
- Synthetic tests cover NOP/RET decoding, unaligned/reversed/out-of-bounds windows; authentic-main tests retain the whole-file SHA guard and CLI report replay.
- Falsifiable hypothesis: both targets are paired synchronization/service entrypoints operating on the same object subobject at X0+0x18. Reject the lock/unlock interpretation unless their exact instruction windows and any resolvable imports/call graph show a matching acquire/release contract. An unresolved indirect call, unknown function extent, or absent import evidence leaves the semantics unresolved.
- No runtime hook, native object write, or release flag change is authorized by this static evidence.

## Current execution boundary

Code parent before this slice: `0e84462e75faa2912bca6a5698987d38d23920eb`. The new source/test/workflow commit is initially recorded as PENDING_CI. Final CI run/job IDs and the service-window SHA256 are to be filled only from the authentic Foundation Actions artifact/log.
