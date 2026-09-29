# NSC2Switch Runtime R179 — Corrected D-Pad F30 Eligibility Parity

Parent: exact R178 source package. R172 UJ, P128 exact 30-word runtime delta, R164 StageInfo baseline, and R175–R177 diagnostics remain unchanged.

## Hardware reason for R179

R178 mapped the PC MovesetPlus D-pad-enable field `actor+0xF30` to Switch `actor+0xF20` by extrapolating a -0x10 layout shift from unrelated fields. Hardware falsified that extrapolation.

Before R178, R175/R177 selector traces show `f30=1` for both Left and Right. Under R178, opcode13 writes `F20=1` while `F30` becomes/stays 0 at the selector, and the user reports the intended Left disappearance/transition no longer occurs. Right still selects mode3/candidate922 and remains non-invulnerable.

## Exact R179 delta

1. Event236 opcode13 (`me_enable_dpad_animation`) writes the source field directly at Switch `actor+0xF30`.
2. Native Switch gate at `main+0x59CEB4` is patched from `actor+0xE54 == 124` to `actor+0xF30 == 1`.
3. R178 F20 mapping is retired.
4. Non-UJ opcode23 remains V2H-safe-suppressed for this A/B. No action922 insertion, descriptor clone, PlayAction force, visibility force, damage force, or char281 branch is added.

## Expected markers

- `[NSC:R179] READY parity=1 dpad_enable_off=0xf30 ...`
- `[NSC:R179] DPAD_ENABLE ... f30=...->1 f20_observed=...`
- Existing R175/R176/R177 markers remain enabled.

## Test

Fresh boot Left once, save full log. Fresh boot Right once, save full log.

Primary A/B questions:
- Does Left intended disappearance/secret-room transition return?
- Does selector see `f30=1` again?
- Does Right mode/candidate behavior change with the corrected eligibility gate?

Do not test UJ-dispatch or add action922 repair until this A/B is closed.
