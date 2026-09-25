# NSC2Switch MASTER CHECKPOINT — R129 / P116A
Date: 2026-09-25
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
Restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

## Locked through P114
- P89 generic admission bridge remains required.
- Custom Tobi intended action708 is legitimate and must not be suppressed.
- P107 direct state137 and P108 state136 mappings remain retired.
- P109/P110 proved native state137 comes from a type10 cinematic manager and failing Tobi has no type10 manager.
- P113 proved one successful vanilla UJ entered main+0x7EF098 from return 0x77C5EC and created session9/session10; Tobi in that run never entered 0x7EF098.
- P114 proved in that same 0x77C corridor the type9 preflight returned 0, so type9 was not the blocker.

## P115 correction
P115A used three inline hooks and failed boot due trampoline allocation exhaustion. Retired.
P115B used one inline hook at 0x77C474 and booted (`probe_ok=1`), but a separate successful vanilla char33 UJ reached native 710 with zero P115B EVT_GATE rows. Therefore 0x77C474/0x77C5E8 is only one upstream corridor, not a universal cinematic-session producer.

## Static full xref correction
Paired-main scan proves exactly six direct BL callsites to main+0x7EF098:
- 0x0D6BDC -> return 0x0D6BE0
- 0x0FBF60 -> return 0x0FBF64
- 0x32F570 -> return 0x32F574
- 0x753CB8 -> return 0x753CBC
- 0x77C5E8 -> return 0x77C5EC
- 0x802634 -> return 0x802638

The type10-specific creator main+0x7514AC still has exactly one direct caller, main+0x7EF1B0, inside the outer/inner setup path.

## P116A design
Parent P96. One whole-function trampoline only at main+0x7EF098, a boundary already proven boot-safe by P113.
Logs incoming caller return/bucket, actor/peer identity and action/state, native return, and session9/session10 pre/post.
Read only. Orig(actor) exactly once. No manual session creation, state/action mapping, force708/710, or char281 branch.

## Decision
- Successful vanilla creates s10 from one of six caller buckets; failing custom has no P116 call: back-slice that specific native producer, not the 0x77C corridor generically.
- Custom reaches P116 but s10 remains0: inspect inner 0x7EF128 blockers/peer context for that exact caller.
- Custom creates s10: root moves downstream of registration.
