NSC2Switch P128A R144 — static precise gate cave + persistent post-outer proof

Purpose
=======
P127 kept Naruto UJ and victim-UJ safe, but Tobi still emitted only the P124 GATE
rows and later P125 CLEANUP session=0/mature=0. Artifact audit proved all P127
static downstream branch patches were present. Therefore P128 tests the remaining
unproven assumption: whether the callback-side W8 raw->10 overlay actually changes
the native event-type branch at main+0x77C480.

P128 paired-main gate cave
==========================
0x77C480 now branches to an in-function cave at 0x77C4B8. The block is safe for
this A/B because P127 already forces 0x77C4B4 -> 0x77C514, so native flow never
falls through 0x77C4B8.

Cave policy:
- raw 10: pass (native)
- raw 11: pass (native)
- raw 15: pass only when attacker char id > 280 and < 0x1000 AND action == 707
- raw 24 and every other raw value: reject to native 0x77C5F0

Accepted flow returns to native 0x77C484 actor-C48. All P127 downstream native
calls remain one-call native and the P127 A/B branches stay open:
- actor C48 reject 0x77C494 NOP
- peer C48 reject 0x77C4A8 NOP
- type9 result 0x77C4B4 -> B 0x77C514
- lookup result 0x77C520 -> B 0x77C59C
- native BL 0x77C5E8 -> 0x7EF098 preserved

Runtime hooks
=============
Only these proof hooks are newly active in the P128 install chain:
- P124 GATE at 0x77C474 (strict semantic/opposite/appended logging + persistent arm)
- P128 POST_OUTER at 0x77C5EC
- P125 CLEANUP at 0x7EB27C
Old P124 AFTER_ACTOR/AFTER_PEER/TYPE9 reach hooks are not installed.

P128 READY also prints the actual in-memory words for the static gate/cave and
critical downstream instructions so deployment is proven at runtime.

Safety invariants
=================
- no char281 gameplay branch
- no callback-side C48/type9/lookup/0x7EF098 call
- no direct 0x7EF098 call
- no force708/710
- no game-memory state/session/action field write
- P50 VIS_SHADOW / CTRL14_SHADOW preserved
- P89 generic admission preserved
- P125 state137 fallback remains session-qualified + mature-context-qualified

Test order
==========
1. Naruto own UJ once.
2. Tobi as victim of UJ once.
3. Tobi own UJ once through the failure/cinematic point.
4. Save log immediately; do not use recovery jutsu first.

Expected decisive markers
=========================
[NSC:P128A] READY ... rt480=1400000e rt4b8=7100291f ...
[NSC:P124A] GATE ... raw=15 ...
[NSC:P128A] POST_OUTER ... ret=...
[NSC:P125A] CLEANUP ... session=... mature=...

If POST_OUTER appears with ret=1, native 0x7EF098 finally ran and succeeded.
If POST_OUTER still does not appear while READY runtime words match, the next
frontier is a non-returning/native helper path inside 0x77C484..0x77C5E8, not the
raw event branch.
