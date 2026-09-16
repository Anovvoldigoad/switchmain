NSC2Switch P39A — O14 ACTOR-LOCAL CONTROL DIRECT A/B

Parent:
  P38A O12+O14 shadow baseline.

Why P39A exists:
  P38A is a HARD PASS for Tobi as victim of Naruto slot1, Isshiki, Naruto Sage,
  and Kakashi Ultimate Jutsu. P37A (O12 shadow only) still failed Naruto slot1
  and Isshiki. Therefore the old live O14 route is causally implicated.

Root semantic mismatch:
  Old P35/P37 O14 route called main+0x751134(p3), ignoring actor and p2.
  UltimateStormAPI SC1.70 source me_enable_control(actor, enemy, control) instead
  selects self/enemy and writes an actor-local boolean control flag.

Recovered layout evidence:
  PC SC1.70 control base: player+0x12A34.
  Established PC->Switch player layout delta in this region: -0x10.
  Historical Switch full-port direct-control helper already used player+0x12A24.
  P39A therefore tests the actor-local Switch base +0x12A24.

P39A gameplay delta vs P38A:
  - O12 remains shadow/no-op (P37A proved it is not the victim-UJ cause).
  - O14 is re-enabled ONLY as actor-local direct writes.
  - O15 remains no-op.
  - O2/O3/O4/O8/O13/O22/O23 remain unchanged.
  - No character ID 281/Tobi gameplay hardcode.

O14 control selector map, relative to actor+0x12A24:
   0 +00 attack
  19 +04 far attack  (PC source also falls through to selector1/UJ)
   1 +08 Ultimate Jutsu
   2 +10 jutsus
   3 +18 projectile attack
  18 +1C chakra projectile
   4 +20 grab
   5 +24 substitution
   6 +28 guard
   7 +2C chakra load
   8 +30 movement/chakra
   9 +34 jump
  10 +38 ninja movement
  11 +3C air dash
  12 +40 land dash
  13 +44 D-pad items
  14 +48 leader switch
  15 +4C awakening
  16 +50 supports
  17 +58 counter attack

Safety:
  A candidate control field is written only when its current int32 value is 0 or 1.
  Otherwise P39A logs the rejected value and leaves memory unchanged.
  p2 must resolve self (0) or enemy (1); invalid target resolution is fail-closed.

Runtime markers:
  [NSC:P39A] READY ... vis12_shadow=1 ctrl14_direct=1 control_base=0x12a24 ...
  [NSC:P39A] CTRL14_DIRECT actor=... target=... p2=... p3=... rel=... old=... wrote=...

Hardware acceptance:
  1. Naruto slot1 UJ -> Tobi must remain visible/playable.
  2. Isshiki UJ -> Tobi must remain visible/playable.
  3. Kakashi/stage-cinematic UJ optional repeat -> Tobi must remain normal.
  4. Tobi StageMove must remain PASS.
  5. Send fresh full Uzuy log.
  6. Check CTRL14_DIRECT: expected old values should be 0/1 and wrote=1.

Important:
  P39A is intended to finalize O14 semantics. It is NOT expected to fix awakening
  in this exact run because P38A logged zero O14 selector15 calls across 233 O14
  events. Tobi's own Kamui is also still tracked separately.
