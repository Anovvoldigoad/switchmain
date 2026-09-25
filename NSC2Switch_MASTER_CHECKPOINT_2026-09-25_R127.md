# NSC2Switch MASTER CHECKPOINT — R127 / P115A
Date: 2026-09-25
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID main: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## Locked results through P114A
- P89 generic admission bridge remains required.
- Custom Tobi legitimate graph remains 700 -> 707 -> 708. Action708 must not be suppressed.
- P107 125->137 can force 710 but bypasses cinematic/session lifecycle and breaks audio/stage/visibility/post-UJ state.
- P108 125->136 replays707 and is retired.
- P109 proved native request137 caller return 0x74FF7C inside type10 manager phase3.
- P110 proved successful vanilla UJ runs type10 cinematic manager while failing Tobi own-UJ runs no type10 manager.
- P111/P112 victim125/126/action12 route is matchup-specific, not universal; do not use it as root.
- P113 proved successful vanilla calls outer cinematic-session setup 0x7EF098 from caller return 0x77C5EC, creating session9 and session10; custom Tobi never calls 0x7EF098.
- P114 moved upstream to the type9 preflight query at 0x77C4B0 -> 0x750860. Runtime: exactly one focused preflight in the successful vanilla UJ and it returned 0. Custom Tobi produced no focused preflight at all. Therefore type9 is not the blocker; Tobi diverges before 0x77C4B0.

## Current exact frontier
Static paired-main chain immediately before the type9 query:
- 0x77C474 LDR W8,[X20,#0x50] — event type source.
- 0x77C478 normalizes by clearing bit0; 0x77C47C compares with10; 0x77C480 bypasses unless event type is10/11.
- 0x77C484..0x77C490 calls actor vslot+0xC48; 0x77C494 bypasses on W0==0.
- 0x77C498..0x77C4A4 calls peer vslot+0xC48; 0x77C4A8 bypasses on W0==0.
- 0x77C4AC/0x77C4B0 queries active session type9.
- downstream successful corridor reaches 0x77C5E8 -> 0x7EF098 -> type10 creation.

## P115A design
Parent: P96. P114 whole-function trampoline is removed.
Three read-only inline hooks, zero new whole-function trampolines:
1. main+0x77C474 replaces only the native LDR W8,[X20,#0x50], reproduces the same W8 value, logs raw/normalized event type and pass/fail plus actor/peer identity.
2. main+0x77C490 replaces actor C48 BLR. Calls the exact native virtual target once with the live argument register set, copies native result back to W0, then logs result/target.
3. main+0x77C4A4 same for peer C48 BLR.

Generic focus only: action700..710, state136/137, or semantic UJ. No char281 branch.
No branch rewrite, no session creation, no state/action writes, no force708/710.
P50 victim-safe Event236 shadows remain inherited.

## P115A decision matrix
- Custom has no EVT_GATE row: divergence is earlier than 0x77C474.
- Custom EVT_GATE pass=0: exact root frontier is event type not10/11.
- Custom event passes but ACTOR_C48 ret=0: actor C48 readiness gate is root frontier.
- Custom actor passes but PEER_C48 ret=0: peer C48 readiness gate is root frontier.
- Custom passes all three gates but still no type9 query: unexpected branch/corridor divergence between 0x77C4A8 and 0x77C4B0; inspect exact instruction flow.

## Test discipline
Run one successful vanilla UJ, then one Tobi own-UJ until absorb/stuck. Do not recover with shuriken/jutsu before saving log.
