# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R105

## Current target
Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70.
Program ID `0100FA10190A0000`, main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`.

## Locked hashes
- paired patched main: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore vanilla main: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch: `229bbd6`

## Runtime conclusions through P99A
- Correct custom UJ sequence is `700 -> 707 -> 708 -> 710 -> cinematic`.
- P97 guard was falsified: blocking 708 holds 707 and later exits through unrelated cleanup/action150.
- P98B proved state125 is requested while custom is already in action708; state125 then leads to 261 and 74. This is downstream fallback, not the original missing-710 cause.
- P99A proved vanilla control and custom use the same virtual implementations for slots `+0x1278/+0x12C8/+0x12D0/+0x1988`.
- Vanilla char91 successful UJ reaches PlayAction710 from caller `main+0x7E6EC8`.
- Custom char281 reaches native 707->708 from `main+0x7725D0`, but no 710 is observed before fallback cleanup.
- Therefore focus moved upstream to the proven native action710 producer corridor.

## P100B — one-shot action710 route sweep
Goal: collapse all remaining broad diagnosis into ONE runtime round before a fix candidate.

P100B parent: P96. P97/P98/P99/P100A installers are not active.
P100B is read-only with respect to actor/action/state memory and uses inline hooks only.
No force708, no force710, no action rewrite, no char281 gameplay branch.

### Route landmarks
- `0x488B24` unique direct caller wrapper before native function
- `0x7E6500` native function entry after frame setup; captures mode in W1
- `0x7E6520` mode0 target
- `0x7E664C` mode2 target
- `0x7E6768` mode1 target
- `0x7E6814` common prelude
- `0x7E6880` common path
- `0x7E6A58` final action710 branch family entry
- `0x7E6B08` return from actor vslot +0xC48
- `0x7E6B10` nonzero side of C48 branch
- `0x7E6BB4` zero source-field path
- `0x7E6C34` participant lookup return
- `0x7E6C50` 0x76BDC0 remapper return
- `0x7E6D0C` C48-zero target
- `0x7E6D58` state-not-0x13 target
- `0x7E6EA8` exact native construction `MOV W1,#710`

### Test protocol — one session
1. Boot/menu/battle.
2. Use vanilla char91 and perform UJ until cinematic succeeds.
3. Use custom Tobi and perform UJ until normal failure after action708.
4. Send one log + one compiled artifact.
5. Compare the ordered `[NSC:P100B] ROUTE` path for vanilla vs custom. The last shared landmark / first missing landmark identifies the exact native divergence.

After this run, do not schedule another broad trace. The next build should be a narrowly-scoped fix candidate based on the exact divergence.

## Important architecture rules
- Generic/data-driven. No gameplay `char_id == 281` branch.
- Preserve P50 victim-safe Event236 shadow and P89 actor-predicate admission bridge.
- Do not globally patch wrapper `0x772594`.
- Do not force action700/708/710.
- Do not write E94/E9C/BDA4/BDA8 speculatively.
- Runtime proof before gameplay writes.
