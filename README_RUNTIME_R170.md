# NSC2Switch Runtime R170 — Native UJ707 Gate Probe

R169 is retired as a symptom-level workaround. R170 performs **no whiff action mutation**.

Static Switch v1.70 proof shows the native 707 state handler at `main+0x7E48E4` calls `main+0x769A4C`. A zero return stays in action707; a nonzero return looks up action708 and dispatches it through the native actor vslot `+0xF98`.

R170 hooks only `main+0x769A4C`, preserves `Orig()` exactly, and logs the exact custom-player action707 caller (`LR main+0x7E48E8`). It also reconstructs the three gate causes without writes: animation flag (`anim+0x70 bit0` when `anim+0x50` is present), actor busy field `+0x1264`, and the final animation timing predicate using `anim+0x74/+0x78/+0x80`.

The R169 `707→77→74` release is removed. V2M stage observer hooks are also omitted in this diagnostic build because R164 stage behavior is already hardware-PASS; this lowers perturbation/log overhead. R164 CPK and P128 runtime patch remain unchanged.

Expected marker:
`[NSC:R170] UJ707_GATE ... ret=0 reason=anim_flag70|actor1264|timing ...`

Test one clean UJ miss and do not press movement for ~8–10 seconds, then exit and upload the full log.


## Compile-clean revision
This package removes stale unused local variables left by retired R167/R168/R169 diagnostics. No R170 runtime behavior, hook target, fingerprint, gate condition, or mutation policy is changed.
