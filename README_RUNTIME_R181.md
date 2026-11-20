# NSC2Switch R181 — D-Pad Full Eligibility Rollback

R181 is the complete recovery A/B after R180 hardware showed that restoring the native Switch D-pad gate alone was insufficient. R180 still wrote Event236 opcode13 to actor+0xF30, while the pre-R178 R175 hardware baseline executed opcode13 without a field mutation.

R181 therefore restores both sides of the pre-R178 eligibility behavior:
- native `main+0x59CEB4` remains untouched (`actor+0xE54`, compare `#124`), and
- Event236 opcode13 is shadow-only/read-only with zero F20/F30 writes.

Everything else remains frozen: R172 UJ parity, exact 30-word P128 runtime patch, R175/R176/R177 diagnostics, R164 StageInfo asset baseline, and non-UJ opcode23 suppression.

## Hardware test
1. Fresh boot.
2. Confirm `[NSC:R181] READY full_rollback=1 ... writer13_mutation=0`.
3. Press **Left D-pad once only**.
4. Save the full log and report whether Tobi again disappears/transitions toward the secret room.

Do not test Right in the same boot for this A/B.
