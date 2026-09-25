# NSC2Switch MASTER CHECKPOINT — R126 / P114A
Date: 2026-09-25
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID main: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## Locked runtime results through P113A
- P89 generic UJ admission remains required and inherited.
- Custom Tobi intended graph legitimately reaches 700 -> 707 -> 708. Action708 must not be suppressed.
- P107 125->137 can force native 710 but skips the native cinematic/session lifecycle; resulting cinematic has broken audio/stage/visibility/post-UJ control. Retired.
- P108 125->136 re-enters state136 and immediately replays 707. Retired.
- P109 proved native request137 originates from cinematic-manager caller return 0x74FF7C.
- P110 proved successful vanilla UJ has a type10 cinematic manager while failing Tobi own-UJ has no type10 manager invocation.
- P111/P112 victim125/126/action12 route is not universal. P112B observed a separate successful vanilla UJ without any 0x7EB270 call. Do not use victim125/126 as the generic root.
- P112B exact Tobi cleanup remains downstream: 0x7EB270 is called on attacker Tobi at action708 from caller return 0x7EAF94, then 708->261->74.

## P113A decisive result
P113A was active (`probe_ok=1`). Across the complete runtime log it recorded exactly one cinematic-session setup invocation:
- successful vanilla attacker char129, action707/state136;
- caller return `main+0x77C5EC` (BL at 0x77C5E8);
- native return=1;
- active session type6 `0->0`;
- session type9 `0->1`;
- session type10 `0->1`;
- peer side1 char63 action74/state1.

Failing custom Tobi char281 still ran 700->707->708->125->261->74 but produced ZERO P113 SESSION rows. Therefore Tobi is not calling 0x7EF098 and is not merely being rejected inside the type10 creator. Root is upstream of 0x7EF098.

## Static back-slice of vanilla caller 0x77C5EC
Native corridor immediately before `0x77C5E8 -> 0x7EF098`:
- `0x77C474..0x77C480`: event field +0x50 normalized by clearing bit0 must equal 10 (accepts event type10/11), otherwise branch away.
- `0x77C484..0x77C494`: actor virtual slot +0xC48 must return nonzero.
- `0x77C498..0x77C4A8`: peer virtual slot +0xC48 must return nonzero.
- `0x77C4AC MOV W0,#9`; `0x77C4B0 BL 0x750860`: query existing session type9.
- nonzero type9 result branches around the downstream cinematic setup corridor.
- when type9 result is zero, native continues through `0x77C514 -> 0x795ED0 -> 0x7F78FC`, further participant/pairing work, then eventually `0x77C5E8 -> 0x7EF098`.

## P114A design — read-only exact type9 preflight provenance
Parent: P96, preserving P50 victim-safe behavior and P89 admission.
Exactly one whole-function trampoline at `main+0x750860` (native session query).
Because this function is hot, the hook captures x30/LR first and immediately returns native for every call except:
- caller return exactly `main+0x77C4B4`;
- requested session type exactly 9.

Focused log:
`[NSC:P114A] PREFLIGHT n=... type=9 ret=... caller_off=0x77c4b4`

No actor/state/session writes. No manual type10/session creation. Native query args/return preserved. No forced708/710. No char281 branch.

## P114A decision tree
- Vanilla must emit focused PREFLIGHT, expected ret=0 before its successful type10 setup.
- Custom emits no focused PREFLIGHT during own-UJ -> custom never reaches the type10/11 + dual-C48 preflight path; next frontier is before 0x77C4B0 (event type/C48 selection).
- Custom PREFLIGHT ret!=0 -> existing type9 session is the exact blocker.
- Custom PREFLIGHT ret=0 but still no cinematic/type10 setup -> type9 is not the blocker; next frontier is downstream `0x795ED0 -> 0x7F78FC` / pairing corridor before 0x77C5E8.

## Test discipline
1. One successful vanilla UJ.
2. One Tobi own-UJ through absorb/stuck/fallback.
3. Do not use recovery shuriken/jutsu before saving the log.
4. Run `python3 analyze_p114a_log.py uzuy_log.txt`.
