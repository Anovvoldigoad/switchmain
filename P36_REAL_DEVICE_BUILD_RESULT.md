# P36 actual Android / Termux build result — 24 October 2026

Source: user-supplied real Termux console output after the alignment fix, commit `879f642`.
This report records the user's result without bundling any game binaries.

## Confirmed offline

- P36 Python unittest suite: **16/16 pass**.
- Stock `patch/170/common.cpk`: **728/728** extracted, 346.20 MiB read, 1018.78 MiB decoded.
- Tobi `data/moddingapi/Tobi_Switch.cpk`: **93/93** extracted, 165.91 MiB read/decoded.
- The carrier's alignment `0x200` was correctly propagated to `fastcpk-rebuild pack`; the earlier error about default `0x800` is resolved.
- New output: **93/93** rebuilt in template mode, **67.03 MiB** stored; 81 CRILAYLA-compressed entries; encryption enabled.
- The new output was re-extracted successfully: **93/93**, 67.03 MiB read, 165.91 MiB decoded.
- Build status: `BUILT_AND_VERIFIED_OFFLINE_NOT_GAMEPLAY_TESTED`.
- All 93 path names and numeric IDs remained unchanged; **90 decoded entries unchanged**, and **exactly 3 decoded battle-global entries changed** to the original Switch stock payloads:
  - `data/spc/conditionprm.bin.xfbin`
  - `data/spc/damageprm.bin.xfbin`
  - `data/spc/privateCamera.bin.xfbin`

### SHA-256 (from user's P36 build JSON)

- Verified original Switch 1.70 `common.cpk`: `a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27`
- Input original Tobi carrier: `e61bdb5faf60be186828769a1d064c98f0682ed02f39c6b9929eaab8e7ef69b7`
- Rebuilt P36 candidate: `c6a0d8c88ff36b13bd18372b4f6faac17fc5907c01ab52881d4a1d9fc9dd0bc0`

Candidate filename: `Tobi_Switch_P36_STOCK_BATTLE_GLOBALS_UNTESTED.cpk`.
The user has this candidate locally at
`/storage/emulated/0/Download/P36_TOBI_BUILD_FIXED/`.

## Experimental interpretation — caution

The candidate is **not yet verified at runtime**. There is no evidence that these three overrides explain disappearing enemies. Keeping all 93 paths avoids changing binder routing by deleting paths.

**Important encoding confound:** original carrier extraction reported
`cc2=1, crilayla=0` (the vast majority of carrier payloads appear unencrypted/uncompressed on disk according to FastCPK counters), whereas the P36 candidate extraction reported
`cc2=93, crilayla=81`. The **decoded** 90 non-target resources match, but the new CPK's stored encoding differs from the original. Therefore a difference in runtime behavior between original and P36 could reflect changed packaging/loader handling as well as the three parameter changes. This is not proof of any encoding defect.

Next phase: run a reversible, controlled A/B check with exactly one carrier change, keeping the existing subsdk9 bridge, same emulator/driver, same enemy/map and no other mod changes. Back up the original active carrier and revert if boot, menu, combat or actor rendering regresses. Record visibility, Tobi animation and crashes. An identity repack with the same encryption/compression settings would provide a stronger control for attributing runtime changes specifically to the three globals.

**No claim of playable Tobi, no ROMFS-only autonomous mount, and no native render-root-cause proof.**
