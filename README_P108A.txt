NSC2Switch P108A — post-708 state136 lifecycle bridge (R119)

Purpose
=======
P107A proved that exact state125 -> state137 is sufficient to produce native
PlayAction710 and enter the Kamui cinematic, but log51 showed the cinematic
lifecycle is incomplete: stale E98/BDA state, no normal 711+ continuation,
enemy/stage/control defects, and Event236 voice opcode26 remains unported.

P108A corrects the state bridge itself before any per-symptom patching.
It maps the SAME exact post-708 cleanup request 125 -> state136, not 137.
Native state request/commit and all controller dispatch remain intact.

Why state136
============
Pinned v1.70 state table and relocation proof:
  state125 -> vslot +0x4C0 -> main+0x7DDD94
  state136 -> vslot +0x518 -> main+0x7E47B8
  state137 -> vslot +0x520 -> main+0x7E64D4

The +0x518 controller is the native UJ setup controller. Static fingerprints
inside it include action708 plus participant setup actions136/138/137. Native
state137/+0x520 then contains the PlayAction710 producer.

P108A guard (all required)
==========================
  caller return 0x7EB28C
  requested state 125
  arg2=1, arg3=0
  player side0
  semantic UJ active
  generated OugiAwakening membership
  action708
  E94=63, E98=136, E9C=0
  BDA4=1, BDA8=0, BDC8=0

Safety
======
- exactly one new trampoline at main+0x7A89A4 (same budget as P107A)
- no direct E94/E9C/BDA/control write
- no force708 / no force710
- no char281 gameplay branch
- P50 victim-safe Event236 shadows preserved
- P89 generic admission bridge preserved
- P107A runtime hook retired

Known independent parity gap
============================
Event236 opcode26 (me_play_voice_string) is still intentionally unported in
this lineage, so audio is NOT the pass/fail criterion for P108A. First validate
that native state136 lifecycle restores stage/participant/control/exit behavior.

Test
====
1. Fresh boot; READY must show map125_to136=1.
2. Tobi own UJ once.
3. Confirm BRIDGE req=125 mapped=136.
4. Look for native progression through setup and then PlayAction710.
5. Check whether Tobi regains control, enemy survives/returns, and stage restore
   is improved.
6. Victim-UJ regression once.

If P108A reaches native 710 with healthy post-UJ lifecycle, freeze the state
bridge and port Event236 opcode26 audio separately.
