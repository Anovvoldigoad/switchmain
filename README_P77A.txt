NSC P77A — LOW-VOLUME UJ ACCEPTANCE PROBE

BASELINE
========

P77A preserves the complete P67A behavioral baseline.

P76A runtime established an important fact:

  main+0x8B2B70 ret=1

immediately preceded native:

  requested=700
  PlayAction700

on a successful vanilla Ultimate Jutsu.

P76A also revealed a diagnostic limitation:
the hot per-frame corridor loggers reached their n<512 limits before
the later Tobi XXA attempt.


P77A TARGET
===========

Only the native UJ acceptance helper is actively probed:

  target:
    main+0x8B2B70

  exact active caller return:
    main+0x7F4648

Static ABI:

  uint32_t(void* actor)


P77A CALLBACK
=============

The trampoline always:

  1. reads diagnostic state;
  2. calls Orig(actor);
  3. reads diagnostic state again;
  4. logs qualifying evidence;
  5. returns the native result unchanged.

Logging occurs at the exact active caller when:

  - semantic selector1 is active; OR
  - native helper return is nonzero; OR
  - E94 changes; OR
  - E9C changes.

There is NO global n<512 hot-loop cap.


PURPOSE
=======

Capture the actual native helper result during the real Tobi XXA
attempt immediately before the engine requests action445.


REFERENCE
=========

Expected successful vanilla sequence:

  P77A UJ_ACCEPT ret=1
      ->
  requested=700
      ->
  PlayAction700

Target Tobi question:

  semantic selector1 = 1

Does main+0x8B2B70 remain ret=0 before requested445?


NO GAMEPLAY FORCE
=================

P77A contains no:

- char281 gameplay branch
- state87 forcing
- action700 forcing
- selector8 override
- F58 override
- inline BLR replacement
- raw Event236 restore


TARGET BUILD
============

Nintendo Switch
Naruto x Boruto Ultimate Ninja Storm Connections
Update 1.70

Build ID:

48ece454b61412b9fb46fab2be3f5ef7b2804f39
