# NSC2Switch MASTER CHECKPOINT — R125 / P113A

## Target
Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70, Program ID 0100FA10190A0000.
Paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`.
Restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.

## Locked results through P112B
- P89 admission bridge remains required and generic.
- Custom Tobi legitimate action graph includes 700 -> 707 -> 708.
- P107 direct 125->137 can force 710 but bypasses native cinematic/session lifecycle and breaks audio/stage/visibility/post-UJ restore.
- P108 125->136 replays 707 and is retired.
- P109 proved vanilla state137 request originates from cinematic manager caller 0x74FF7C.
- P110 proved successful vanilla UJ runs a type10 cinematic manager while custom Tobi own-UJ runs no type10 manager at all.
- P111 observed one matchup where victim Tobi used 125->126->12 before cinematic manager.
- P112B corrected that over-generalization: a separate successful vanilla UJ versus victim char96 reached 710 without any 0x7EB270 call. Therefore victim125/126/action12 is not a universal UJ prerequisite.
- P112B exact custom cleanup: 0x7EB270 is invoked on attacker Tobi at action708 from caller return 0x7EAF94; peer is already stuck in a non-cinematic state. This remains downstream cleanup, not the root.

## New universal frontier: type10 session registration
Static v1.70 backtrace:
- `0x74F698`: manager record type check; type10 dispatches through `0x74F6AC -> 0x74F954`.
- `0x7514AC`: type10-specific registration wrapper. It hard-codes `W1=10`, calls generic record inserter `0x750C78`, then stores context to record+0x34.
- Unique direct BL caller of `0x7514AC` is `0x7EF1B0`.
- `0x7EF128` checks active type9 and type6 via `0x750860`, resolves peer via `0x796384`, derives context from peer+0xCB8, then calls `0x7514AC`.
- `0x7EF098` is the outer actor setup wrapper and the P113A probe boundary.

## P113A design
Parent: P96 (therefore preserves P50 victim-safe + P89 admission).
Exactly one whole-function trampoline: `main+0x7EF098`.
Read-only observations:
- incoming LR / caller_off captured before helpers;
- actor identity/action/E94/E98/E9C/E50/BDA4/BDA8/BDC8;
- peer identity/action/E94/E9C;
- active session type6/type9/type10 before and after native call;
- native return from `Orig(actor)`.

No manual call to 0x7514AC/0x750C78. No state or action writes. No forced 708/710. No `char==281` branch.

## Decision tree
- Vanilla shows type10 0->1; Tobi has no relevant P113 invocation: missing upstream call to 0x7EF098; use vanilla caller_off to back-slice producer.
- Tobi reaches 0x7EF098 and returns 0 with type6 or type9 active: blocker identified.
- Tobi reaches 0x7EF098, type6=0/type9=0, ret=0, type10 remains0: next probe inner 0x7EF128 / peer-context branch.
- Tobi creates type10 but still fails: divergence is downstream of registration.

## Test discipline
One successful vanilla UJ, then one Tobi own-UJ until absorb/stuck. Do not use recovery shuriken/jutsu before saving log.
