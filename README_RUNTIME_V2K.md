# NSC2Switch Runtime V2K — Recovery Baseline + Passive D-Pad Snapshot

Target: Storm Connections Switch v1.70 / original main.

V2K is a deliberate recovery build after V2J hardware produced broad regressions that the user could not cleanly enumerate. It returns gameplay behavior to the V2I hardware baseline and keeps only passive logging that does not install a new inline hook or add a new native stage call.

## What V2K rolls back from V2J

- Removes the V2J inline probe at `main+0x7E74A4` entirely. V2J installed the probe but hardware log32 produced zero `DPAD_NATIVE_CONSUMER` callbacks, so it added risk without yielding frontier evidence.
- Removes the V2J `main+0x48E61C` post-stage/member-sweep call from the custom stage bridge. V2J hardware executed that extra call on `STG_2TOB_UNI_LT` and `STAGE_SI45A`; the user reported many new bugs. V2K restores the V2I stage sequence: `HandleStageChange -> Fix actor -> Fix enemy`, with `poststage=0`.

## Preserved V2I behavior

- Original main on disk + exact validated 30-word runtime delta.
- Seven dynamic resolver anchors and P128 UJ admission/session path unchanged.
- Safe opcode23 suppression retained; no full PL_ANM930 call.
- V2I diagnostic activation core retained (`SW_MTOB_XH` + Right=100.0f only for the exact action77/SPTYPE_ACTION10 fixture).
- Opcode26 native SFX playback retained unchanged because hardware confirmed Tobi UJ sound works.
- No force-visible, no global no-damage, no force708/710, no char281 gameplay branch.

## New passive evidence

At the existing V2I activation-core point V2K records:
- actor+0xF30 before/after;
- all four D-pad charge words before/after;
- E94/E98;
- animation state at 0x1268.

Marker: `[NSC:V2K] DPAD_PASSIVE_SNAPSHOT`.

This adds reads/logging only. It does not install the V2J F30 inline hook and does not add any extra gameplay write beyond the already-existing V2I activation-core diagnostic.

Stage marker: `[NSC:V2K] STAGE_SAFE_BASELINE ... poststage=0`.
Boot marker: `[NSC:V2K] READY ...`.

## Locked hashes

Original/restore main SHA256:
`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

Reference P128 main is verifier-only; never deployed.
