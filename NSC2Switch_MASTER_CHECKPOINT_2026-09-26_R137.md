# NSC2Switch MASTER CHECKPOINT — R137 / P121B
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID main: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
P120 paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
P121B paired main SHA256: f9a8a10f757987b353d7ddcf3a9a74621a8db2398fd6820d09ac280cae72070a
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## P120 hardware result
P120 boots and its corrective gate fires on custom UJ:
- action707 semantic custom attacker
- appended damage idx1848 raw15
- P120 bridge=1 changes only W8 raw15 -> out10
- later idx1847 raw24 is not bridged by one-shot guard
- custom still progresses natural 707 -> 708 and no custom 710/cinematic lifecycle is observed.
Thus the type10/11 event gate is not sufficient by itself; frontier is downstream.

## P121A boot failure
P121A attempted a second inline hook at main+0x77C4A4 (peer C48 BLR).
Fresh boot log reaches `[NSC:P120A] READY ... patch_ok=1`, then aborts before any
P121 READY with:
- hook_impl.cpp:602
- `Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)X`
This repeats the known trampoline-allocation ceiling previously seen with P115A.
P121A is retired as an invalid runtime architecture; it provides no C48 gameplay result.

## P121B design
P121B uses no extra P121 hook/trampoline. The paired main changes one instruction:
- main+0x77C4A8 native `CBZ W0,0x77C5EC` (0x34000A20)
- P121B `NOP` (0xD503201F)
The preceding native peer C48 virtual call at 0x77C4A4 remains intact.
P120A remains the sole new runtime inline hook and the only custom-specific gate.
No B9E4/event/damage/session/action/state write, no direct 0x7EF098 call, no force708/710,
no char281 gameplay branch.

P121B is a behavior-changing causal A/B, not final policy, because the peer reject
branch is statically bypassed for every type10/11 corridor entry that reaches it.
If cinematic starts, final repair must move upstream to generic readiness semantics.
