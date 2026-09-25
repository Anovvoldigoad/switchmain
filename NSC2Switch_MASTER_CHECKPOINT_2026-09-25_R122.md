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
