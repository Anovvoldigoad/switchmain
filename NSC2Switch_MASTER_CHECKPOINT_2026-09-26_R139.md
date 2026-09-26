# NSC2Switch MASTER CHECKPOINT — R139 / P123A
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID main: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## Locked runtime through P122
- P119: custom semantic action707 produces appended damage records 1848/raw15 and 1847/raw24; control successful UJ uses raw10 family.
- P120: first custom raw15 is successfully overlaid to W8=10 (`bridge=1`), but no cinematic/710 follows.
- P121B: static peer-C48 reject bypass at 0x77C4A8 boots and has no effect.
- P122A: static actor+peer C48 reject bypasses at 0x77C494/0x77C4A8 boot and still have no effect. Therefore C48 rejection alone is not the final blocker.
- Custom still takes legitimate natural 707->708. Never suppress/force708.

## Exact static corridor after C48
0x77C4AC MOV W0,#9
0x77C4B0 BL 0x750860 (type9 query)
0x77C4B4 CBZ W0,0x77C514
- nonzero route exits to 0x77C5EC without 0x7EF098.
- zero route continues.
0x77C518 BL 0x795ED0
0x77C51C BL 0x7F78FC
0x77C520 CBZ X0,0x77C59C
- non-null route performs alternate handling and exits at 0x77C598 -> 0x77C5EC.
- null route 0x77C59C eventually reaches 0x77C5E8 BL 0x7EF098.
Successful vanilla historical proof: type9 preflight returned 0 and successful outer setup reaches 0x7EF098.

## P123A design
P123A retires P121B/P122 static-global C48 NOPs; paired main returns to baseline 1adc4dfe...34de0.
Compact runtime install path keeps P50/P67/P81 + direct P89 functional behavior and skips read-only P82/P84/P85/P88B hook layers to free trampoline capacity.
Five inline callsite bridges are conditional on one coherent generic corridor:
- attacker = live X23, victim = live X19;
- attacker custom ID > vanilla max and <0x1000;
- semantic UJ true;
- action707;
- opposite battle side;
- first appended damage record >=1847 arms a per-side plugin-local latch.
Native callees are always executed exactly once before any result overlay.
- 0x77C474: raw non10 -> W8=10 only on first armed appended event.
- 0x77C490: actor C48 native0 -> W0=1 only while armed.
- 0x77C4A4: peer C48 native0 -> W0=1 only while armed.
- 0x77C4B0: type9 native nonzero -> W0=0 only while armed.
- 0x77C51C: helper native non-null -> X0=0 only while armed.
Native 0x77C5E8 -> 0x7EF098 remains untouched.
No char281 hardcode, no game-memory field write, no session/action/state write, no direct 0x7EF098 call, no force708/710.

## Runtime decision
Expected ordered markers:
GATE -> ACTOR_C48 -> PEER_C48 -> TYPE9 -> LOOKUP.
First missing marker = exact frontier.
If all five appear and 710/cinematic starts, inspect native return values to tighten final generic repair.
If all five appear but no 710/cinematic, move inside 0x7EF098/session lifecycle and do not revisit raw damage/B9E4/C48/708.
