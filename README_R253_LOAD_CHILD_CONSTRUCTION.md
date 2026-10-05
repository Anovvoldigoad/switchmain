# NSC2Switch R253 — Load child construction trace

R253 follows R252 hardware proof that the target reaches Wait with `[self+0x140]=1` but `[self+0x188]=[self+0x190]=0`.

This is a read-only diagnostic. Keep the exact R250 `sound.cpk` carrier. Use clean game `main`, external `Tobi_Switch.cpk` OFF, ID281 OFF, and replace only diagnostic `subsdk9`.

Expected markers:
- `[NSC:R253] READY ...`
- `[NSC:R253] TARGET_REGISTRY_CAPTURE ...`
- `[NSC:R253] LOAD_VECTOR ...`
- `[NSC:R253] SOURCE_LIST ...`
- `[NSC:R253] CANDIDATE_RESOLVE ...`
- `[NSC:R253] CHILD_PRODUCER ...`

Hardware protocol:
1. cold boot;
2. hover vanilla briefly;
3. move directly to native-ID46/Tobi diagnostic target;
4. hold at least 10 seconds;
5. exit and save the full Uzuy log.
