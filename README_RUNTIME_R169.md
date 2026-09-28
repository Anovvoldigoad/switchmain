# NSC2Switch Runtime R169 — UJ707 Whiff Release

R168 hardware showed that the true Tobi UJ miss does not reach the 740→74 cinematic cleanup boundary. The actual miss path is `74→700→707`; action 707 then persists indefinitely until player movement forces `707→77`.

R169 arms only when a custom semantic UJ enters `707` from `700`. It does not use a blind wall-clock timeout. The runtime waits until the native action phases settle to the observed terminal whiff signature (`e80=1`, `e94=8`, `e98=8`, `e9c=0`, `bda4=1`, `ea4>=100`). If a native hit transitions out of 707 first, the latch is cancelled.

On terminal whiff, R169 uses the already-proven direct animation core for a two-tick release: `707→77`, then on the next P81 tick `77/78→74`. No full movement PlayAction is injected, so movement events/position changes are not intentionally generated.

Expected markers:
- `[NSC:R169] READY ...`
- `[NSC:R169] UJ707_WHIFF phase=arm ...`
- `[NSC:R169] UJ707_WHIFF phase=release77 ...`
- `[NSC:R169] UJ707_WHIFF phase=release74 ...`
- or `phase=cancel-native` / `phase=cancel-state` when the native hit path wins.

Test:
1. Keep R164 fixed CPK.
2. Build/install R169 runtime.
3. Fresh boot.
4. Trigger Tobi UJ and intentionally miss. Do not touch movement.
5. The 707 loop should self-release after the native terminal phase settles.
6. Then test one UJ hit to verify the 707→710 hit path is not interrupted.
