# NSC2Switch MASTER CHECKPOINT — R136 / P121A
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Main Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## P120A hardware result — partial causal PASS
Fresh runtime `uzuy_log(15).txt` plus compiled P120 artifact prove:
- P120 loaded with `patch_ok=1`.
- Custom Tobi semantic action707 hit appended damage idx1848/raw15.
- P120 one-shot bridge executed: raw15 -> W8/out10 with trace gap1.
- Cinematic still did not start; no Tobi code710 appeared.
- ~34 ms later second custom damage raw24 remained native and natural 707->708 occurred.
Therefore event-type gate failure was real but not sufficient. The live blocker is now downstream of 0x77C480 and before native cinematic lifecycle completion.

## Static downstream corridor
- 0x77C484..0x77C490 victim/actor vslot+0xC48; 0x77C494 rejects on W0==0.
- 0x77C498..0x77C4A4 peer vslot+0xC48; 0x77C4A8 rejects on W0==0.
- 0x77C4B0 type9 query.
- 0x77C5E8 -> 0x7EF098 outer cinematic-session setup.

## P121A corrective design
P121 retains P120 gate bridge and adds exactly one corrective inline hook at peer C48 BLR main+0x77C4A4.
The hook calls the exact native virtual target once with live X0..X7. It changes only returned W0, and only when:
- P120 one-shot latch is armed for the same peer actor/side;
- peer is generic custom ID > vanilla max and <0x1000;
- semantic UJ active and action707;
- native peer C48 returned 0.
Then out W0=1. Native true is preserved. No actor/event/B9E4/session/action/state write. No direct 0x7EF098 call. No force708/710. No char281 branch.

## Interpretation
- `PEER_C48 bridge=1` + cinematic/710 => peer readiness gate causal and P121 is the candidate generic bridge.
- P120 `GATE bridge=1` but no P121 `PEER_C48` => victim/actor C48 at 0x77C490 rejected before peer call; next corrective site is actor C48, not event gate.
- P121 reached with native/out nonzero but still no cinematic => peer gate already passes; next frontier is type9/outer setup corridor.
