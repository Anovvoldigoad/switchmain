# NSC2Switch MASTER CHECKPOINT — R140 / P124A
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID main: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## P123 runtime result / retirement
- P123A booted with compact parent and all five installs reported ready.
- Tobi custom action707 produced P123 GATE bridge=1 for appended damage, but no P123 ACTOR_C48 / PEER_C48 / TYPE9 / LOOKUP marker appeared.
- Vanilla char83 reached native action710, while the user observed a later UJ freeze/regression.
- P123 replaced native BL/BLR callsites and invoked their callees from callback context. Even when outputs were not overlaid for vanilla, that changes native caller/LR provenance. P123 downstream call-replay architecture is retired.
- P50 victim-safe VIS_SHADOW / CTRL14_SHADOW and P89 generic semantic bridge remain required.

## P124A design
- Compact functional parent remains P81 + direct P89.
- Main is restored to paired native hash; P121/P122 static NOPs are absent.
- Keep only the proven conditional custom semantic-707 appended-damage gate at 0x77C474.
- Never hook or replay the native calls at 0x77C490, 0x77C4A4, 0x77C4B0, 0x77C51C, or 0x77C5E8.
- Add native-safe reach checkpoints only at simple instructions:
  - 0x77C498 LDR X8,[X23]: AFTER_ACTOR, captures native actor-C48 W0 before replaying the LDR.
  - 0x77C4AC MOV W0,#9: AFTER_PEER, captures native peer-C48 W0 before replaying MOV.
  - 0x77C514 MOV X0,X19: TYPE9_ZERO, proves the zero branch from native type9.
  - 0x77C5E4 MOV X0,X23: OUTER_REACH, proves native execution is immediately about to call 0x7EF098.
- No callback-side native calls. No LR/caller substitution for the cinematic corridor.
- No char281 branch, no game-memory writes, no B9E4 write, no direct session/action/state mutation, no force708/710.

## Decision matrix after one Tobi own-UJ
- GATE bridge=1, no AFTER_ACTOR -> actor/victim C48 returned zero: exact blocker = first C48 gate.
- AFTER_ACTOR present, no AFTER_PEER -> peer C48 returned zero: exact blocker = second C48 gate.
- AFTER_PEER present, no TYPE9_ZERO -> native type9 returned nonzero: exact blocker = type9 gate.
- TYPE9_ZERO present, no OUTER_REACH -> divergence inside 0x77C514..0x77C5E4 lookup/branch region.
- OUTER_REACH present, still no cinematic/710 -> native call reaches 0x7EF098; next frontier is inside outer session setup.

## Regression discipline
Test in this order on a fresh boot:
1. one vanilla Naruto UJ (must no longer freeze),
2. Tobi as victim of vanilla UJ (must remain safe),
3. one Tobi own-UJ until it sticks or enters cinematic.
