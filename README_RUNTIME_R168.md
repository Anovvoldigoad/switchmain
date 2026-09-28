# NSC2Switch Runtime R168 — UJ Miss Animation Direct Bounce

R167 hardware result: the exact miss hook fired and changed PlayAction(74) a2 from -1 to 0, with logical action and ANM1268 both reaching 74, but the visible Kamui animation still looped. About 50 seconds later, the first real movement transition 74->77 released the stale visual.

R168 therefore retires the R167 a2 experiment. The native UJ cleanup PlayAction(74,-1) is preserved unchanged. On the same exact custom-UJ miss signature only, after native cleanup returns successfully, R168 calls the proven direct-animation core (main+0x766320) with animation 77 then 74, both using (-1,0,rate=1.0). It does not invoke full PlayAction for the bounce, so movement events/position changes are not intentionally generated.

Markers:
- `[NSC:R168] READY ...`
- `[NSC:R168] UJ_MISS_ANM_BOUNCE phase=arm ...`
- `[NSC:R168] UJ_MISS_ANM_BOUNCE phase=post ... anm=740->74->77->74 ...`

Frozen: R164 CPK/stage fix, P128, opcode26, voice, D-pad.
