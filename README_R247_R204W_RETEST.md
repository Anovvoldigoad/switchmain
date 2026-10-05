# NSC2Switch R247 — R204W State-Table Retest on R245C Carrier

Purpose: reuse/reconstruct the already-authorized R204W four-state `ccUiCharacterSelect3DModel` tracer after the materially changed R245C real-Tobi graph made the Load update callback reachable and R245G proved native `state5c=2 / phase6c=1`.

This is diagnostic-only and read-only.

Installed hooks (9 total):
1. `main+0x1161B88` target `mtobcharsel.xfbin` owner-register capture
2. Load enter `main+0x548094`
3. Load update `main+0x549804`
4. Create enter `main+0x549868`
5. Create update `main+0x54991C`
6. Wait enter `main+0x549950`
7. Wait update `main+0x549B80`
8. Select enter `main+0x549C40`
9. Select update `main+0x549EA8`

No CPK bind, no main patch, no gameplay patch, no ID patch, no path rewrite, no return override, no state writes.

The historical standalone R204W source ZIP referenced by R246 was not available in Library, so this package is a reconstruction from the proven callback offsets/contract in R246 on top of the boot-proven R245G source tree. Do not claim byte identity with the historical R204W ZIP.

## Hardware protocol
- Keep exact R245C real-Tobi native-ID46 carrier.
- Keep clean game `main`.
- External `Tobi_Switch.cpk` OFF.
- ID281 OFF.
- Replace only diagnostic `subsdk9` with the GitHub Actions artifact from this source.
- Cold boot.
- Hover one working vanilla preview briefly.
- Move directly to Tobi/native-ID46 target.
- Hold 10+ seconds.
- Exit and preserve full log.

Expected log markers:
- `[NSC:R247] READY ...`
- `[NSC:R247] TARGET_REGISTRY_CAPTURE ...`
- `[NSC:R247] STATE_CALL state_name=Load|Create|Wait|Select callback=enter|update phase=pre|post target=...`

Use `python3 analyze_r247_r204w_log.py <log>` to classify the run.
