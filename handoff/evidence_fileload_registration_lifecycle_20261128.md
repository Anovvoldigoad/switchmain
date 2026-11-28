# FileLoad registration-helper and alternate-tail trace — VERIFIED_CI_STATIC_ONLY

Date: 2026-11-28  
Code HEAD: \`2b06a49730dc3bdf9816cc7f4f984231aa34b4fe\`  
Code parent: \`3982db7cbea721a3308870945cd29dad6598a5ba\`  
Original Switch v1.70 main Git blob: \`8af900db0d7003255b4ddb3cbd1289cd5a15458e\` (27,701,509 bytes)  
Original main SHA256 verified by CI: \`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9\`

## Research-first primary sources

- [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), tag \`502c38d3ee832509f9ee3951b7d3339826538fec\`; previous 2.1.2.0 tag \`a4a6e7e2aeec79cffa7d477e4b1a8fcd05823983\`. The full compare has one non-generated C# source change in \`ViewModel/TitleViewModel.cs\`; no SkillCustomizeParam/XFBIN parser delta.
- [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1), tag \`789fe96f99cdaa77f952b90b563c6e3f49b6d697\`; previous \`dfe371dd4f1f0d1d1ad74a79e1bc8192a6d1fc31\`. Inspected source blobs: \`SkillEditorModel.cs\` e165471682e4a7aed91094ef07f92df271f31639, \`SkillEditorViewModel.cs\` 870af492c41f26c2aab07c216b6fa5fd00ac2cbf, \`ConditionPrmModel.cs\` 2827ca9e484eafb0c7435f066d42ff3e9345e17c, \`XfbinParser.cs\` 86c63708edf2698b5bc1c2a54c0480cce014b525. The inspected skill/XFBIN parser files are unchanged across the release tags.
- [UltimateStormAPI 2.1.2.1](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc), commit \`a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc\`, parent \`1c3460573fa70b595e6bfa70e52f83f1c3f74f12\`; \`MovesetPlus.cpp\` blob d7c5dbbebd60415f8d304321f083897658a86146. The 2.1.2.1 diff adds command 29, \`TakeOverEnemyProjectiles\`: it queues recently active projectile pointers for a 250 ms takeover window under a Windows mutex; later PC hooks transfer owner/collision identity. This Windows x64 implementation is not Switch ABI evidence.
- [PyCriCodecs CPK reference](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111), commit \`755055ee7b056c9c1aefc6505a3daa3e45e2e111\`: \`cpk.py\` blob 2ed2cbb2c6112124013ab52755dba8a443e91306 and \`utf.py\` blob d1662d140a48cae37a6696213ee441aed4076edb. It reads CRI CPK metadata and TOC/ITOC/HTOC/GTOC/HGTOC offsets; format reference only, not Switch archive precedence.
- [REA](https://github.com/morluto/rea/tree/0386efd1e1dfa41af41f804a6be56c6f5b7615d4), commit \`0386efd1e1dfa41af41f804a6be56c6f5b7615d4\`: evidence-workflow methodology only, not target ABI.
- The branch-pinned original main is the exact 27,701,509-byte Git blob above; the CI analyzer refuses any SHA256 other than the pinned value.

## Verified byte-level observations

1. At \`0x116b810\`, the caller directly BLs \`0x290\`. The bounded helper CFG uses an atomic load/increment and writes a 24-byte record: \`x8\` at offset 0, \`x1\` at offset 8, \`x2\` at offset 16. The registration arguments resolve to a text-relative pointer candidate \`0x116b888\`, BSS object candidate \`0x43717e0\`, and data/context pointer \`0x1eb3000\`. The two data pointer cells \`0x2143460\` and \`0x2143468\` each have one \`R_AARCH64_RELATIVE\` relocation to \`0x2161230\`; the atomic counter is at \`0x21620d8\`. Runtime relocated table values and record invocation order are not known.
2. The registered code-pointer candidate \`0x116b888\` has a 0x100-byte bounded CFG (SHA256 \`877fcd30e1fb00f75bf143dfb499419122edb72acf95677b73219ee7f0a809ec\`). It walks 64 eight-byte slots beginning at \`0x4371800\`, directly calls \`0x116b390\` for each slot, then clears 0x200 bytes through sixteen 32-byte stores. This is a cleanup candidate, not a proven destructor; callback identity, function extent and invocation order remain false.
3. Static initialization guard \`0x43717d8\` and object candidate \`0x43717e0\` are tied to PLT/GOT imports \`__cxa_guard_acquire\` at \`0x12f3690\` and \`__cxa_guard_release\` at \`0x12f36a0\`. Runtime guard state and imported implementation/provider are not proven.
4. Alternate tail \`0x116d830 -> 0x12f49b0\` resolves through GOT slot \`0x2142888\` / \`R_AARCH64_JUMP_SLOT\` to mangled symbol \`_ZN2nn3mem17StandardAllocator4FreeEPv\` (\`nn::mem::StandardAllocator::Free(void*)\`). Its receiver pointer cell \`0x215d2e8\` has one \`R_AARCH64_RELATIVE\` relocation to BSS address \`0x4371a00\`; the alternate path copies X0 to X1 at \`0x116d824\`, with the caller trace showing X0 originated in X19. The runtime allocator object, pointer type, ownership contract and imported implementation are unresolved.
5. Index-error path \`0x116b864 -> 0x12155a0\` materializes rodata address \`0x1ae9d22\` and passes exact bytes \`BlockManager::GetBlock break\\n\`. The target's function identity is not asserted.

## CI evidence

- Code commit: \`2b06a49730dc3bdf9816cc7f4f984231aa34b4fe\`
- Parent: \`3982db7cbea721a3308870945cd29dad6598a5ba\`
- [GitHub Actions run 46086093686](https://github.com/Anovvoldigoad/switchmain/actions/runs/46086093686), run #2: COMPLETED SUCCESS.
- Job \`verify\`: \`140795884030\`; original raw job log inspected. Marker: \`PINNED_FILELOAD_REGISTRATION_LIFECYCLE_PASS helper_stride 24 cleanup_slots 64 alternate_symbol _ZN2nn3mem17StandardAllocator4FreeEPv NO_DESTRUCTOR_NO_ABI_NO_UZUY_CLAIM\`.
- Artifact: [15238478983](https://github.com/Anovvoldigoad/switchmain/actions/runs/46086093686/artifacts/15238478983), ZIP 12,850 bytes, SHA256 \`7e6362c66972f6d35588a73c6ae25cc9aed3d6285b674d9ef479a4789bd87fd3\`.
- Report JSON: 173,233 bytes, SHA256 \`51fb342cffdb2b39ea7d3c72aa21c21afcb20b6ea1c979a15f91eba4de74c949\`.
- Only the isolated FileLoad lifecycle workflow ran on this code HEAD. Foundation/Factory/Compressed/Moveset PASS suites were not rerun; path filters keep unrelated suites dormant for this FileLoad-only change.

## Explicit limits / next proof

No native consumer ABI, BR X2 target, vtable identity, object type, callback/destructor identity or invocation, ownership/lifetime, lock/unlock, async completion, rollback/unbind, archive precedence, imported implementation, emulated ARM64 or Uzuy result is established. No runtime hook was added. \`full_moddingapi=false\`, \`ready_for_gameplay_test=false\`, \`emulator_tested=false\` remain unchanged.

Next: resolve the dynamic object/vtable value feeding \`BR X2\` at \`0x116b3d0\` without assuming a C++ object layout; locate the runtime/static writer for the 64 slots and determine whether a read-only Uzuy memory snapshot is available. If not, continue a separate source-grounded PC-to-Switch semantic consumer slice. Do not patch or hook this path until allocation ownership, callback and teardown are proven.
