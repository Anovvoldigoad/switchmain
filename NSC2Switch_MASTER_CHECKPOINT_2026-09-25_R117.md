# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R117

## Locked target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Locked conclusions — do not reopen without contradictory runtime proof
- P50 victim-safe Event236 shadow remains required.
- P89 solved generic UJ admission; custom natively reaches `700 -> 707 -> 708`.
- Action708 is required and must not be suppressed.
- P98B proved state125 is explicitly requested during action708 from caller `0x7EB28C`.
- P101 holding state125 did not produce 710; therefore state125 is not the missing-710 producer.
- P102 holding action74 restored movement but did not produce cinematic/710; action74 is downstream.
- P99 proved cleanup/state125 occurs after the missing handoff; relevant virtual topology matches vanilla.
- P103 specialCond factory remap `281 -> 58` executes but does not produce 710.
- P104 `0x7EE8E0/+0x12240` gate hypothesis is retired for this failure path.
- P105B proved custom state125 enters +0x4C0 mode0 and that invocation produces `708 -> 261`; this is downstream cleanup.
- Vanilla successful UJ produces 710 from `main+0x7E6EC8` inside +0x520 `main+0x7E64D4`.

## Method correction
Vanilla char91 uses `700 -> 707 -> 710`, while required custom Tobi graph is
`700 -> 707 -> 708 -> 710`. Therefore vanilla E94/E9C values must not be blindly
copied onto the custom post-708 phase.

## P106A — decisive remaining question
Replace (do not add to) the P105B diagnostic trampoline:
- retire +0x4C0 hook `main+0x7DDD94`;
- install exactly one trampoline at +0x520 `main+0x7E64D4`.

P106A logs `(actor, mode)` entry/exit, exact caller/callsite, action pre/post,
E60/E70/E90/E94/E98/E9C/EA0/EA4, BDA4/BDA8/BDC8, and both vtable sibling slots.
It is read-only and preserves native arguments/behavior.

## Decision tree
1. No custom action708 CTRL520 invocation -> next target is the upstream controller dispatch/eligibility that should reach the sole direct wrapper `main+0x488B28`.
2. Custom enters +0x520 but no 710 -> next target is first internal branch divergence inside +0x520.
3. Custom enters +0x520 and 710 occurs -> stop diagnosis and validate cinematic/post-710 lifecycle.

No more state125/261/74 suppression experiments unless new evidence contradicts the locked conclusions.
