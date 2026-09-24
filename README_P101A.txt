NSC2Switch P101A — EVENT-DRIVEN 708 END GUARD
=============================================
Purpose
-------
Functional candidate after runtime proof that the required custom graph is
700 -> 707 -> 708 -> 710, and that state125 cleanup preempts action708 before
its Event236 me_play_action (op23) END transition is observed.

Design
------
- Parent: P96A; P100C is not installed.
- Exactly one new trampoline at main+0x7A89A4 (state request), previously boot-proven by P98B.
- Generic gates only: semantic UJ latch + generated OugiAwakening membership + action708 + request125.
- While those gates match and Event236 op23 has not yet been seen, reject state125.
- Event236 op23 is latched before the existing P50 HandleActionAnimation path runs.
- As soon as op23 is seen, the state125 guard fails open.
- Safety fail-open: if EA4 exceeds 0x3000, native state125 is allowed even if op23 never appears.

What P101A does NOT do
----------------------
- no char281 gameplay branch;
- no forced action708 or action710;
- no writes to E94/E9C/BDA4/BDC8/EA4;
- no raw native Event236 restore;
- P50 victim visibility/control shadows remain intact.

Expected decisive markers
-------------------------
[NSC:P101A] READY ... probe=1
[NSC:P101A] HOLD125 ... action=708 ...
[NSC:P101A] OP23 ... text=...END...
[NSC:P50A] ACTION ... found=1 index=710   (if action-data resolves END to 710)
[NSC:P101A] OP23_RESULT ... action=708->710

If op23 never appears, P101A must eventually log PASS125 after EA4 > 0x3000 and return to native cleanup instead of hanging forever.
