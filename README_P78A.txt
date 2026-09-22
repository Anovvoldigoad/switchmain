NSC P78A — SEMANTIC ALT ROUTE PROBE

BASELINE
========

P78A preserves P77A.

P77A preserves P67A behavioral safety and probes the native UJ helper
at main+0x8B2B70.

P77 runtime proved:

successful vanilla UJ:
  0x8B2B70 ret=1
  -> requested700

failing semantic-enabled Tobi route:
  no active 0x8B2B70 UJ_ACCEPT record
  -> requested445

Therefore P78 investigates the upstream alternate route.


TARGET
======

ALT helper:

  main+0x8B2D04

Exact active caller return:

  main+0x7F4598

ABI:

  uint32_t(void* actor)


LOGGING
=======

P78 logs ALT_SEM only when:

  caller == main+0x7F4598

and:

  semantic selector1 is enabled.

Native behavior is always preserved:

  ret = Orig(actor)
  return ret


PURPOSE
=======

Determine whether the semantic-enabled failing actor enters the ALT
path immediately before requested445.

If ALT_SEM is observed while P77 records no UJ_ACCEPT for the same
actor during that attempt, the early route divergence is runtime-proven.


NO GAMEPLAY FORCE
=================

No:

- char281 gameplay branch
- state87 forcing
- action700 forcing
- helper-return forcing
- selector8 override
- F58 override
- inline BLR replacement
- raw Event236 restore


TARGET
======

Nintendo Switch
Naruto x Boruto Ultimate Ninja Storm Connections
Update 1.70

Build ID:

48ece454b61412b9fb46fab2be3f5ef7b2804f39
