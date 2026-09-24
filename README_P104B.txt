P104B — SIBLING-CONTROLLER TWO-GATE POST-PREDICATE PROOF (READ ONLY)

Purpose
-------
Fix the P104A timing ambiguity and identify the first native gate that differs
between a successful vanilla UJ and the failing custom Tobi UJ after action708.

Static proof
------------
+0x4C0 -> main+0x7DDD94, the controller that produced runtime 708->261.
+0x520 -> main+0x7E64D4, sibling controller containing native PlayAction710.
Before the 262/261 selector, +0x4C0 evaluates:
  gate1: BL main+0x7EE8E0; CBZ return
  gate2: LDR W8,[actor+0x12240]; CBZ return
Only both nonzero can continue toward the 262/261 path.

Why P104B exists
----------------
P104A sampled actor+0x12240 before Orig(actor), while native +0x4C0 reads the
field only after predicate 0x7EE8E0 returns. P104B keeps one whole-function
trampoline but samples gate2 both before and after Orig(actor). gate12240_post is
the authoritative P104B sample for diagnosis.

Instrumentation
---------------
Exactly one new whole-function trampoline at main+0x7EE8E0.
- Capture X30/caller before helper calls.
- Non-target callers: execute Orig(actor) and return without actor-state reads.
- Exact caller 0x7DE028 only.
- Player side only (side==0).
- gate12240_pre sampled immediately before Orig(actor).
- native predicate executes exactly once and its return is never changed.
- gate12240_post sampled immediately after Orig(actor), before post-state reads.
- Focus actions 700..711.
- Log pre/post action/state and vtable +0x4C0/+0x520 targets.
- No actor/action/state/gate writes, no force708/710, no char281 gameplay branch.
Parent is P96; P101/P102/P103 are not installed. P50/P89 lineage remains as in P96.

Test protocol — ONE session
---------------------------
1. Boot and confirm [NSC:P104B] READY ... probe=1.
2. Vanilla char91: perform one successful UJ through cinematic.
3. Custom Tobi: perform one UJ through 700->707->708 until normal failure.
4. Send the single log plus compiled artifact/subsdk9.
5. Run: python3 analyze_p104b_log.py <log>

Validation
----------
Analyzer rejects rows unless:
- side == 0
- caller_off == 0x7DE028
- slot4c0_off == 0x7DDD94
- slot520_off == 0x7E64D4

Decision
--------
pred=0:
  gate1 is closed; +0x4C0 takes the first early return.

pred!=0 and gate12240_post=0:
  gate1 is open, sampled gate2 is closed.

pred!=0 and gate12240_post!=0:
  both sampled gates are open; +0x4C0 may continue toward 262/261.

gate12240_changed=1:
  predicate execution changed gate2; diagnose using POST, not PRE.

The first reproducible vanilla/custom gate difference in the same run becomes
the next functional target. P104B itself remains observation-only.
