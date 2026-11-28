# PC MovesetPlus numeric command delta — 2.1.2.1

Date: 2026-11-28  
Branch: port/full-api-v170  
State: VERIFIED_UPSTREAM_PC_SOURCE_ONLY_CI

Code commits: 51b8b50928809942e3efe238056bbf422c78edaa; b7df04c64fb41c1403cb8b456164aeb9a45a9d6c

## Research-first primary sources

| Source | Exact ref | Retrieved identity |
|---|---|---|
| [NSC-ModManager release 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) | tag commit 502c38d3ee832509f9ee3951b7d3339826538fec; pinned main 276116ebf5ba398a867793cb02ee6c33c0927645 | XfbinParser.cs Git blob faf79d588fd8beb3f5761faebedd2252853b2f2b is identical at tag and project pin. The release is dated 2026-08-30 and describes Switch Projectiles Target. |
| [NSC-Toolbox release 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/releases/tag/2.1.2.1) | tag commit 789fe96f99cdaa77f952b90b563c6e3f49b6d697; pinned main 6f780cb6814f07e03c16b3e78d97dde4e4368983 | XfbinParser.cs blob 86c63708edf2698b5bc1c2a54c0480cce014b525, SkillEditorModel.cs blob e165471682e4a7aed91094ef07f92df271f31639, and Properties/Program.cs blob 9d5f3e0dfa4ed51cf7924b503081a87b12146f64 match between tag and pin. |
| [UltimateStormAPI 2.1.2.1 source](https://github.com/TheLeonX/UltimateStormAPI/tree/a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc) | commit a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc; parent 1c3460573fa70b595e6bfa70e52f83f1c3f74f12 | MovesetPlus.cpp blob d7c5dbbebd60415f8d304321f083897658a86146; parent blob e96af51210e96926a7bdaa70c44b6645f1a2b2b6; header blob 74f6ff6c0243a01d7e49d8565c9933089b8c7a2c. |
| [PyCriCodecs](https://github.com/t-wy/PyCriCodecs/tree/755055ee7b056c9c1aefc6505a3daa3e45e2e111) | commit 755055ee7b056c9c1aefc6505a3daa3e45e2e111 | cpk.py blob 2ed2cbb2c6112124013ab52755dba8a443e91306 and utf.py blob d1662d140a48cae37a6696213ee441aed4076edb; independent CPK/TOC/ITOC/@UTF format reference only. |
| [REA](https://github.com/morluto/rea/tree/76e319b80fe207f05b6558053a8f66264680820d) | latest inspected main commit 76e319b80fe207f05b6558053a8f66264680820d | supported-targets blob b4fad121e917a1a6eb148e72c4ac1daef7d95265 and binary-diagnostics blob 76da9004df7abee2831a2b1d9bc32e99d0e03f1c. This is offline ELF64 little-endian AArch64 / Switch NSO-NRO metadata tooling, not runtime register capture. |
| Pinned Switch v1.70 original main | repository blob 8af900db0d7003255b4ddb3cbd1289cd5a15458e, 27,701,509 bytes | Required SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9. It was rehashed by the prior targeted FileLoad CI run 46124030962/job 140914501509; this command-registry slice does not modify or rehash game bytes. |

## Verified upstream delta

The pinned PC MovesetPlus dispatcher at lines 651-659 contains:
- case 27 -> SetProjectileDeflection(a1, true)
- case 28 -> SetProjectileDeflection(a1, false)
- case 29 -> TakeOverEnemyProjectiles(a1)

The comparison parent source contains cases 27 and 28 and SetProjectileDeflection, but no case 29 or TakeOverEnemyProjectiles. Therefore Start/Stop Deflect are not new in 2.1.2.1; the new Switch Projectiles Target release feature maps to numeric PC meTest command 29.

The separate NSC-Toolbox Properties/Program.cs catalog remains 289 NS4 names and 300 NSC names (289 identical prefix entries plus 11 NSC-only names). These ME_* name indices are not the numeric meTest command IDs 27-29. No ME_* index is assigned to the projectile commands.

## PC-only implementation facts (not transplanted)

SetProjectileDeflection reads the PC player-side field at offset 0xE60 for GameVersion 1.70 (0xC88 otherwise), accepts side 0 or 1, and atomically toggles projectileDeflectionEnabled[side].

TakeOverEnemyProjectiles reads the same PC-specific side field, selects the opposite side, uses GetTickCount64 and g_deflectProjectileMutex, drops active projectile handles older than 250 ms, and queues pending takeovers expiring at now + 250 ms. The queueing loop does not dereference the cached projectile pointer. The source uses Windows-specific types/APIs including __int64, IsBadReadPtr, GetTickCount64, and std::mutex. These offsets, mutexes, clocks, object fields and PC hook logic are not a Switch ABI.

## Implemented capability and falsifiable checks

- Added a separate machine-readable numeric command registry and CLI modes --commands / --command-id.
- Kept the existing 289/300 ME_* name-index catalog unchanged.
- Tests assert exact source commit/blob identities, parent-vs-pin presence of commands 27-29, command 29's 250 ms/Windows mutex evidence, strict ID boundaries, and separation from ME_* indices.
- If command 29 appears in the comparison parent, if cases 27/28 disappear, if source blob pins differ, or if any command is assigned an ME_* index, the regression fails.

## Scope boundary

This is upstream PC source inventory plus host-side registry tests. It does not implement projectile deflection or target switching on Switch. No Switch hook, engine consumer, object ownership, callbacks, lock/unlock pairing, async lifetime, rollback/unbind/destructor, archive precedence, Uzuy or gameplay behavior is claimed. All release flags remain false.


## CI verification — completed 2026-11-28

Final code head: b7df04c64fb41c1403cb8b456164aeb9a45a9d6c (parent 51b8b50928809942e3efe238056bbf422c78edaa). Initial implementation commit: 51b8b50928809942e3efe238056bbf422c78edaa (parent 41a77a98067b411a7575bd3b0b457a250ccd95a8).

- Targeted run [46126953689](https://github.com/Anovvoldigoad/switchmain/actions/runs/46126953689), job 140923548062: COMPLETED SUCCESS; raw job log inspected; 9 tests passed. Artifact 15255972970, ZIP SHA256 c010a30453000e844a6927b359b2c416e2b6da9cfeaa51e9f8156b6a5e6c15fd. The downloaded artifact's internal SHA256SUMS was independently checked and both JSON files passed.
- Offline multi-mod regression run [46126953701](https://github.com/Anovvoldigoad/switchmain/actions/runs/46126953701), job 140923548214: COMPLETED SUCCESS; raw job log inspected; all merge/reassemble/split/source-replay/remove/replace/batch-patch/reorder test suites passed.
- First run 46126791253/job 140923044694 passed 8 tests but its artifact SHA file contained a path prefix removed by upload-artifact. The workflow now writes basenames; a Start/Stop-specific regression was added; the final 9-test run and self-verifying artifact above supersede it.

CI verifies the source-pinned PC command inventory and offline tooling only. It does not verify a Switch projectile consumer or any runtime ABI.
