# NSC2Switch R180 — D-Pad Native Gate Rollback Recovery

R180 is a rollback-only hardware A/B derived from the exact R179 source. R178/R179 attempted to port UltimateStormAPI's PC D-pad eligibility gate into Switch main+0x59CEB4. Hardware R179 proved that restoring the opcode13 writer to F30 did not restore Left behavior, while selector identity remained correct. Therefore the common PC-style gate rewrite is retired.

R180 keeps the proven Event236 opcode13 F30 writer but performs **zero writes** to main+0x59CEB4. It fail-closed verifies the untouched Switch v1.70 words E54 / #124 and then proceeds with the frozen runtime.

Frozen invariants retained: original main, resolver7/7, exact30 runtime delta, P128, R172 UJ SetAnmDirect parity, R164 StageInfo, R175 selector trace, R176 registry trace, R177 descriptor trace, voice skipped. Non-UJ opcode23 remains OP23_SAFE_SUPPRESS.

## Test
1. Fresh boot. Confirm `[NSC:R180] READY rollback=1 native_gate_restored=1 ... gate_patch_words=0`.
2. Press **Left once**. Save full log immediately. Primary question: does the disappearance/secret-room transition return?
3. Optional separate fresh boot: press **Right once**. Right is not expected to be invulnerable yet because non-UJ opcode23 is still suppressed and opcode17 cannot execute.

Do not mix UJ testing into the first Left A/B.
