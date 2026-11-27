# FileLoad PLT/GOT dynamic-symbol evidence — 2026-11-27

## Research-first pins

- PC ModdingAPI source: [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), latest release tag commit \`502c38d3ee832509f9ee3951b7d3339826538fec\`. The repository's pinned source commit \`276116ebf5ba398a867793cb02ee6c33c0927645\` has that release commit as its parent. Existing source comparisons pin SkillCustomizeParamViewModel blob \`ced6d805b207fae16cf68df87e23744608d6562b\` and SkillCustomizeParamModel blob \`6a891e237d27fdf01336f806dbef8767d609a304\`.
- PC editor source: [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1), latest release tag commit \`789fe96f99cdaa77f952b90b563c6e3f49b6d697\`. SkillEditorViewModel blob \`870af492c41f26c2aab07c216b6fa5fd00ac2cbf\` and SkillEditorModel blob \`e165471682e4a7aed91094ef07f92df271f31639\` were already compared with 2.1.2.0 and are unchanged. The 2.1.2.1 release notes add Switch Projectiles Target; this is PC editor/release metadata, not a Switch consumer ABI.
- CRI/CPK reference: [PyCriCodecs](https://github.com/t-wy/PyCriCodecs), commit \`755055ee7b056c9c1aefc6505a3daa3e45e2e111\`; cpk.py blob \`2ed2cbb2c6112124013ab52755dba8a443e91306\`, utf.py blob \`d1662d140a48cae37a6696213ee441aed4076edb\`. These document CPK/@UTF formats only.
- Independent evidence workflow reference: [REA](https://github.com/Black-Star-Pen/REA), commit \`0386efd1e1dfa41af41f804a6be56c6f5b7615d4\`; CLI guide blob \`35f686aa26ba850b56e8a74df648f47d99a164e3\`. This is a generic evidence workflow, not Switch ABI evidence.

## Pinned game input

- Repository: https://github.com/Anovvoldigoad/switchmain
- Branch at start: \`port/full-api-v170\`
- Parent HEAD: \`39fe92c5c8c45463ba3c9e34d84627480b5dbc45\`
- Original main Git blob: \`8af900db0d7003255b4ddb3cbd1289cd5a15458e\` (27,701,509 bytes)
- Required SHA256: \`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9\`
- Prior service report: \`native_fileload_status.json\`, artifact from Foundation run \`46022686334\`, artifact ID \`15210990048\`; exact status-wrapper target window SHA256 \`c173105388fd40288927c87c40b2882abf9a97ff4fcae5f229af50a1cac07461\`.

## Exact instruction evidence

The status wrapper at \`0x1158c90\` calls:
- \`0x1158c9c BL 0x12f4cf0\`
- \`0x1158ca4 BL 0x12f50e0\`
- \`0x1158cbc BL 0x12a35b4\`

The unlock path at \`0x1158d2c\` branches to \`0x12a35bc\`. Both local service adapters are two-instruction windows:
- \`0x12a35b4: LDR X0,[X0]; B 0x12f4d90\`
- \`0x12a35bc: LDR X0,[X0]; B 0x12f4da0\`

Four exact ADRP/LDR/ADD/BR PLT stubs are pinned:

| Role candidate | PLT | 16-byte words (little-endian bytes) | Derived GOT slot |
|---|---:|---|---:|
| thread-context provider | 0x12f4cf0 | \`707200d0 111645f9 10a22891 20021fd6\` | 0x2142a28 |
| lock primitive import | 0x12f4d90 | \`707200d0 113e45f9 10e22991 20021fd6\` | 0x2142a78 |
| unlock primitive import | 0x12f4da0 | \`707200d0 114245f9 10022a91 20021fd6\` | 0x2142a80 |
| thread-token provider | 0x12f50e0 | \`707200b0 111246f9 10823091 20021fd6\` | 0x2142c20 |

For every stub the ADRP+LDR-derived slot must equal the ADRP+ADD-derived address, the LDR destination is X17, and the final branch is \`BR X17\`. The analyzer then looks up exactly one original DT_RELA/DT_JMPREL record for each slot and decodes its ELF64 dynamic-symbol name when the relocation type and symbol metadata permit it.

## Falsifiable claims and limits

- Positive: exact caller branch, wrapper dereference, PLT words, GOT address, relocation record and dynamic symbol name can all be independently reproduced from the SHA-pinned original main.
- Negative: changed words/call targets, non-RELA PLT metadata, malformed symbol bounds, missing symbol terminator, and duplicate slot relocations must be rejected or explicitly reported unresolved.
- A missing relocation is not converted into a guessed symbol. Unknown relocation types do not resolve a function name.
- A symbol name is only the original NSO's dynamic relocation metadata. It does not prove the imported implementation, runtime resolver result, actual function execution, pthread/nn::os semantics, lock concurrency, object lifetime, callback, async completion, rollback, unbind, destructor, archive precedence, or safe native hook ABI.
- No runtime hook is installed. \`full_moddingapi=false\`, \`ready_for_gameplay_test=false\`, and \`emulator_tested=false\` remain unchanged.

## Implementation under CI

- Added \`tools/portlib/native_fileload_imports.py\` and \`tests/test_native_fileload_imports.py\`.
- Foundation workflow executes the original-main analyzer and writes \`native_fileload_imports.json\` into the existing proof artifact.
- Local host checks: Python syntax compilation passed; synthetic PLT address derivation, malformed PLT rejection, relocation-name resolution, missing-slot handling, duplicate relocation rejection, non-RELA rejection, symbol-bound rejection and unknown-relocation handling passed using a minimal isolated helper harness. Authentic NSO integration is pending GitHub Actions.
