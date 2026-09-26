# NSC2Switch MASTER CHECKPOINT — R138 / P122A
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID main: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Paired P122A main SHA256: 520e2452a03a6de9c82a9670c5ed2fe9f7b1bdccd100f1a67de81a92aba0458e
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## New hardware result from P121B
- Boot: PASS; no trampoline abort.
- P121B READY patch_ok=1.
- P120A still bridges custom UJ victim damage idx1848 raw15 -> out10 with attacker semantic=1 action707.
- P121B peer reject branch 0x77C4A8 was statically NOP'd.
- No custom cinematic/710; Tobi still progresses natural 707->708.

Interpretation: peer-C48 reject bypass alone is insufficient. Since actor/victim C48 executes first at 0x77C490 and its reject CBZ at 0x77C494 can prevent the peer call entirely, the next functional A/B is to bypass actor reject as well while preserving both native C48 calls.

## P122A design
- Preserve P120A gate bridge.
- Preserve P121B peer branch NOP at main+0x77C4A8.
- New static patch main+0x77C494: 0x34000AC0 -> 0xD503201F.
- Native actor C48 BLR at 0x77C490 preserved.
- Native peer C48 BLR at 0x77C4A4 preserved.
- Zero P122 hooks/trampolines.
- No B9E4/event/damage/session/action/state write.
- No direct 0x7EF098 call.
- No force708/710.
- No char281 gameplay branch.

## Decision after P122A
- Cinematic/710 appears: actor C48 reject is causally implicated.
- Still no cinematic: both C48 readiness reject branches are excluded; frontier moves to type9 / downstream outer cinematic setup.
