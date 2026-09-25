# NSC2Switch MASTER CHECKPOINT — R128 / P115B
Date: 2026-09-25
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Main Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## Locked runtime through P114
- P89 generic admission bridge remains required.
- Custom Tobi intended action graph includes 700 -> 707 -> 708; do not suppress 708.
- P109/P110 proved native 137 comes from type10 cinematic manager and failing Tobi has no type10 manager.
- P113 proved successful vanilla creates type10 through outer setup main+0x7EF098, called from return 0x77C5EC; failing Tobi never calls 0x7EF098.
- P114 proved vanilla reaches type9 preflight query main+0x77C4B0 and gets ret=0; failing Tobi never reaches that query. Type9 is therefore not the custom blocker.
- Root frontier is now before 0x77C4B0: event type10/11 gate and the two C48 readiness gates.

## P115A retired — boot failure
P115A installed three additional inline hooks at 0x77C474, 0x77C490 and 0x77C4A4.
Runtime aborted during hook installation before P115 READY:
`Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)X`.
This repeats the known hardware/runtime constraint that stacking multiple new
hook trampolines on top of the P96/P89/P50 baseline is unsafe.

## P115B design
Return to P96 functional baseline and install exactly ONE extra inline hook:
- main+0x77C474, replacing only `LDR W8,[X20,#0x50]`.

The callback faithfully reproduces W8 and logs raw_type, norm_type=(raw&~1),
pass=(norm_type==10), actor and peer context. Actor/peer C48 callsites are only
fingerprinted, not hooked. No session/state/action/event/actor memory mutation.
No char281 branch.

## Decision tree
A) Vanilla EVT_GATE appears, custom has none -> divergence is before 0x77C474; back-slice event dispatch/source.
B) Custom EVT_GATE appears with pass=0 -> event type gate is the first concrete divergence.
C) Custom EVT_GATE appears with pass=1 -> event type is correct; next diagnostic is a SINGLE actor-C48 hook only.
