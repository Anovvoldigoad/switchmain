# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R106

## Current target
Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70.
Program ID `0100FA10190A0000`, main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`.
Paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`.
Restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
exlaunch pin `229bbd6`.

## Locked runtime findings
- Correct custom UJ order is `700 -> 707 -> 708 -> 710 -> cinematic`.
- P97 guard was invalid as a fix because blocking 708 causes fallback/positioning corruption.
- P98 proved state125 is requested during action708 from `caller_off=0x7EB28C`; downstream 261 is consequence, not root cause.
- P99 proved vanilla and custom share the same relevant virtual topology (`+1278/+12C8/+12D0/+1988`); cleanup gate is downstream fallback.
- Vanilla successful control reaches PlayAction710 from `caller_off=0x7E6EC8`; custom does not.

## P100B boot failure — decisive
P100B attempted sixteen `HOOK_DEFINE_INLINE` installs. Runtime never reached `[NSC:P100B] READY`.
Immediately after `[NSC:P96A] READY`, exlaunch aborted in `hook_impl.cpp:602` with:
`Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)`.
The subsequent `Unmapped InvalidateNCE ... 0x69696900000000` spam is post-abort fallout.
Therefore P100B is retired and must not be used.

## P100C design
P100C replaces the 16-hook sweep with exactly one whole-function trampoline at `main+0x64942C`.
This helper is called from five distinct sites inside the action710 corridor, so LR identifies the route stage:
- `0x7E6AB4` PRE22
- `0x7E6ACC` PRE19
- `0x7E6AE4` PRE2A
- `0x7E6B20` ROUTE13 (decisive)
- `0x7E6D68` NOT13_RECHECK22
Native code immediately after the decisive call compares W0 with `0x13`.
`ret==0x13` continues toward participant lookup/remap and the proven PlayAction710 path; otherwise native branches away.

P100C preserves Orig exactly once, performs no state/action/control writes, does not force 708/710, and contains no char281 gameplay branch.
Parent is P96A. P97/P98/P99/P100A/P100B are not installed.

## Test
Single session: vanilla successful UJ, then custom Tobi UJ failure. Compare `[NSC:P100C] ORACLE` rows, especially `tag=ROUTE13`.
