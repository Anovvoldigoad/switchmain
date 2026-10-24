# P37 — verified Android build result (24 October 2026)

User-provided Termux execution output after using `build_p37_preserve_carrier.py` from the fetched P37 branch.

## Actual build evidence

- The local `git switch --track origin/research/p37-preserve-carrier-encoding` failed with `starting point ... is not a branch`, consistent with a narrow/shallow checkout configuration. Despite that error, `test_cpk_p37.py` and `build_p37_preserve_carrier.py` were present and executed successfully. Git tracking status **is not** a binary-build failure.
- P37 unit suite: **13 tests passed**.
- Official patch/170 common CPK source: **728/728 extracted**; pinned SHA-256 `a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27`.
- Original working Tobi carrier: **93/93 extracted**; pinned source SHA-256 `e61bdb5faf60be186828769a1d064c98f0682ed02f39c6b9929eaab8e7ef69b7`.
- Rebuilt **93/93**, **165.91 MiB stored**, `CRILAYLA=false`, `Storm encryption=false`, `alignment=0x200`. FastCPK reports zero new compressed files.
- Candidate re-extracted **93/93** in CC2-Storm mode; FastCPK counters: `cc2=1`, `crilayla=0`, the same profile observed with the source carrier.
- `Sorted` packer-generated 1, explicitly restored to **0** to match the original carrier.
- All **93 file paths and numeric IDs identical**. All **90 non-target entries identical in stored bytes** and decoded bytes.
- Exactly three decoded battle-global paths were replaced from stock:
  - `data/spc/conditionprm.bin.xfbin`
  - `data/spc/damageprm.bin.xfbin`
  - `data/spc/privateCamera.bin.xfbin`
- Status `BUILT_AND_VERIFIED_OFFLINE_NOT_GAMEPLAY_TESTED`.
- Candidate SHA-256: `a9dc66fad84fc07c1d29dba08b47e330a756c945c662ed22df201c37506f4a50`.
- User-local output:
  `/storage/emulated/0/Download/P37_TOBI_BUILD/Tobi_Switch_P37_PRESERVED_ENCODING_UNTESTED.cpk`.

## Decision

The P36 packaging confound (93 newly CC2-encrypted / 81 compressed entries) has been removed: P37 retained the 90 untouched entries byte-for-byte and the carrier's unsorted metadata/alignment. However the actual game has **not** been launched with P37; a fully equivalent 93-resource offline round trip still cannot establish loader/gameplay compatibility. The three changed globals are a controlled hypothesis, not a verified root cause.

Next: back up the *installed* old carrier and test P37 as the sole carrier substitution, with the same subsdk9 bridge, emulator/driver, arena, and opponent. First establish boot/menu and then enemy visibility, Tobi animation and battle stability. Restore old carrier immediately on regression. No additional XFBIN edits should be inferred from this report.
