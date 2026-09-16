NSC2Switch P35A — GENERIC EVENT236 CORE
=======================================

PURPOSE
P34A hardware PASS proved native Switch event236 (ME_ENEMY_DISP_OFF) is the direct
cause of the custom-Tobi opponent disappearance / inconsistent hitability and the
old victim-UJ corruption. P34A is diagnostic only because it redirects event236 to
a harmless leaf and therefore discards all UltimateStormAPI MovesetPlus opcodes.

P35A restores the real event236 callback and intercepts it with a generic custom-
character dispatcher. There is NO Tobi/281 character hardcode. v1.70 vanilla max
charID=280 is the generic boundary; custom IDs >280 are routed through MovesetPlus
semantics. Vanilla IDs use the original native event236 callback unchanged.

ACTIVE / SWITCH-PROVEN ROUTES
  2  StageMove          exact historical Switch route
  3  change_skill       exact historical direct field route
  4  change_speed       exact historical actor/enemy +0x214 route
  8  walk_speed         exact historical actor+0x10D34 route
 12  visibility         exact historical actor vtable BC8/BD0 route
 13  dpad_animation     exact historical actor+0xF30 route
 14  enable_control     exact historical main+0x751134 route
 15  disable_control    historical safe Switch behavior = no-op
 22  play_pl_anm        exact historical name/action lookup route
 23  play_action        exact historical pre-action + lookup/play route

All other valid MovesetPlus opcodes 1..29 are shadow/no-op for now. They NEVER fall
back to native ME_ENEMY_DISP_OFF. Invalid/vanilla callbacks preserve native behavior.

TRACE
Every routed custom event236 emits, up to a fixed budget:
  [NSC:P35A] EVT236 actor=... side=... char=... op=... p2=... p3=... p4bits=...

This lets us identify the exact remaining Kamui/awakening opcode sequence without
blindly porting unproven handlers.

IMPORTANT DEPLOYMENT
P34A main currently redirects event236 slot 236 -> event237. P35A therefore MUST
restore the pre-P34A P23A/P32 main before the new subsdk9 can receive event236.

The build artifact includes:
  atmosphere/contents/0100FA10190A0000/exefs/subsdk9   (new P35A build)
  restore/atmosphere/contents/0100FA10190A0000/exefs/main

Expected restore-main SHA256:
  2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

KEEP UNCHANGED
  P33A Tobi_Switch.cpk Sorted=0
  SHA256 e61bdb5faf60be186828769a1d064c98f0682ed02f39c6b9929eaab8e7ef69b7
  existing loose charicon + current params

DO NOT use P34A main together with P35A subsdk9.

HARDWARE TEST ORDER
1. Fresh boot.
2. Tobi vs vanilla opponent: enemy must remain visible + hittable.
3. Trigger the move that should change stage. Report whether stage transition works.
4. Use Tobi Kamui UJ. Report whether cinematic begins and whether victim returns.
5. Try Tobi awakening. Report whether input/state becomes available.
6. Let enemy UJ hit Tobi once: victim flow should stay normal.
7. Stop Uzuy and send the complete fresh log.

EXPECTED READY
  [NSC:P35A] READY cpk=1 trace=1 event236=1 evt=0x816300 ...

DECISION
- StageMove fixed: opcode2 port is validated on current P33A runtime.
- Kamui fixed: identify which active event236 routes completed the handoff.
- Kamui still stuck: inspect EVT236 sequence; port only the missing opcode(s).
- Awakening still unavailable with no relevant EVT236 sequence: move to separate
  Event121/SpecialCond/Ougi/condition-manager activation path; do not force state.
