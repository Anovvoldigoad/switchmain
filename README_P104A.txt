P104A — SIBLING-CONTROLLER TWO-GATE PROOF (READ ONLY)

Purpose
-------
Identify the first native gate that lets custom action708 continue inside vtable
slot +0x4C0 (main+0x7DDD94) toward action262/261 instead of returning early.

Static proof
------------
+0x4C0 -> main+0x7DDD94, the function that produced runtime 708->261.
+0x520 -> main+0x7E64D4, the sibling controller containing native producer710.
Before the 262/261 selector, +0x4C0 evaluates:
  gate1: BL main+0x7EE8E0; CBZ return
  gate2: LDR W8,[actor+0x12240]; CBZ return
Only both nonzero can continue toward the 262/261 path.

Instrumentation
---------------
Exactly one new whole-function trampoline at main+0x7EE8E0.
At exact caller return main+0x7DE028, for actions700..711, logs native predicate
return, actor+0x12240, pre/post state, and vtable +0x4C0/+0x520 targets.
No writes, no return override, no forced action/state, no char281 gameplay branch.
Parent is P96; P101/P102/P103 are not installed.

Test protocol (one session)
---------------------------
1. Boot and confirm [NSC:P104A] READY ... probe=1.
2. With vanilla char91, perform one UJ that reaches cinematic.
3. With custom Tobi, perform one UJ through 700->707->708 until its normal failure.
4. Send one log + compiled artifact.
5. Optional: python3 analyze_p104a_log.py <log>

Decision
--------
pred=0: early return at first gate.
pred!=0 and gate12240=0: early return at second gate.
pred!=0 and gate12240!=0: sibling controller is fully armed to continue toward 261.
The first vanilla/custom difference is the next functional target; this build itself
is observation-only.
