# NSC2Switch MASTER CHECKPOINT — R122 / P111A
Date: 2026-09-25
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID main: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## Locked runtime results through P110
- P89 admission remains inherited and is not the current frontier.
- Tobi intended custom sequence includes legitimate 707->708; action708 must not be suppressed.
- P107 125->137 can produce 710/cinematic but bypasses native cinematic-session setup; result is incomplete/broken lifecycle.
- P108 125->136 re-enters controller136 and replays 707; retired.
- P109 proved native vanilla state137 request caller return main+0x74FF7C, inside type10 manager phase3.
- P110 proved the failing Tobi own-UJ invokes the type10 manager ZERO times.
- Successful vanilla: victim reaches state126 and PlayAction12 @ return 0x7DE9B0 BEFORE manager phase0/2; manager then queues leader137 and paired81 and native 710 follows.
- Failing Tobi own-UJ: victim traverses state39/state121; no victim PlayAction12 and no type10 manager invocation; attacker later falls through 708->125->261->74.

## Root frontier
Victim / participant UJ admission, upstream of type10 cinematic-manager creation.
Need exact provenance of vanilla victim 125/126 versus failing victim 39/121.

## P111A design
READ ONLY, parent P96.
Exactly one new trampoline at main+0x7A89A4 (native request-state gateway).
Focused requested states: 39, 81, 121, 125, 126, 137.
Logs actor identity, side/char, request, caller, native args/ret, action and state pre/post, and vslot E28.
main+0x7A8A9C direct/simple E9C setter is fingerprinted but not hooked.
P110 manager hook is retired; main+0x74F954 stays native.
No request rewrite, no direct state write, no force708/710, no char281 branch.
P50 victim-safe visibility/control shadows remain inherited.

## Decision after runtime
A) Vanilla victim logs req126 -> caller_off is exact state126 producer; compare with Tobi req121 caller.
B) Vanilla commits E94=126 but P111 logs no req126 -> state126 bypasses 0x7A89A4; move provenance to the direct/simple setter family beginning at main+0x7A8A9C.
C) Tobi victim req39/121 caller matches vanilla participant producer but arguments/state differ -> back-slice the producer branch.
D) Tobi victim 39/121 comes from a distinct producer -> compare caller functions before any functional bridge.

Do not return to P107/P108 state forcing unless new evidence invalidates this checkpoint.


# NSC2Switch MASTER CHECKPOINT — R124 / P112B
Date: 2026-09-25

## P111 runtime result — LOCKED
- Successful vanilla victim: req125 @ caller return main+0x7EB28C, then req126 @ main+0x7DDFE4, then PlayAction12 @ main+0x7DE9B0; manager later queues victim81 / attacker137.
- Failing Tobi own-UJ victim: during the actual UJ failure window, req39 then req121 both come from main+0x77CA5C; victim never gets req125/126/PlayAction12.
- Failing attacker Tobi later reaches req125 @ main+0x7EB28C while action708; this is cleanup, not victim admission.
- The extra req121 rows around ~125-127s in the P111 test occurred after the user manually used a stage-switch jutsu to release the stuck victim. They are recovery noise and must not be treated as UJ-root events.
- Manual stage-switch recovery can release the stuck opponent, proving the victim object/lifecycle still exists; it is not permanently destroyed.

## Static lock
- main+0x7EB270 is the whole-function producer that immediately asks the actor for state125 via vslot +0xDF0, return at 0x7EB28C.
- main+0x7DDFD0 asks an already-state125 actor for state126; return at 0x7DDFE4. Therefore state126 is downstream, not the root.
- Blind 39->125 mapping is retired because it would skip the additional native side effects inside main+0x7EB270.

## P112B design
READ ONLY, parent P96.
Exactly one new whole-function trampoline at main+0x7EB270.
Captures incoming LR first, actor side/char/action/E94/E98/E9C/BDA state, native enemy/peer through existing vslot +0xDD0, then calls Orig(actor) exactly once unchanged and records post-state.
No state mapping; no manual invocation of the producer; no force708/710; no char281 branch. P50 victim-safe shadows remain inherited.

## P112 runtime decision
A) Vanilla victim entry appears with caller X; custom victim has no entry; attacker Tobi action708 entry appears with caller Y -> X is the missing victim-admission caller frontier.
B) X == Y but actor roles differ -> back-slice target actor selection immediately before that call.
C) Custom victim does enter main+0x7EB270 -> missing path is downstream inside/after producer, compare post-state/caller.

Do not use stage-switch recovery before capturing the P112 custom-failure window.


## R124 correction
P112A R123 runtime aborted before installing the 0x7EB270 trampoline because sigVictim126 used F9400008 at main+0x7DDFD0. The paired v1.70 main and source verifier both prove the exact word is F9400268. P112B changes only that runtime fingerprint and probe labels/workflow; the target function, read-only behavior, single-trampoline budget, and all gameplay logic remain unchanged.
