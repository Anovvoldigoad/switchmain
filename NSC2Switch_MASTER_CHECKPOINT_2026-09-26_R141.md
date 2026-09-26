# NSC2Switch MASTER CHECKPOINT — R141 / P125A
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
main Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
exlaunch pin: 229bbd6

## Why P107 matters
P107 direct cleanup125->137 proved state137 controller can produce native PlayAction710/cinematic for the custom actor. It also proved blind direct137 is unsafe: context remained stale (E98=63,BDA4=1), audio/stage/visibility/post-UJ lifecycle broke.

## Important correction
P111 victim125->126->12 is not universal. P112B observed successful vanilla UJ with no 0x7EB270 victim call. Therefore P125 does NOT force victim125 or treat it as the universal root.

## Locked upstream evidence
P113 successful vanilla calls 0x7EF098 from 0x77C5E8 and creates session9/type10; custom historically did not. P119/P120 proved custom damage classification raw15 at the bucket5 gate is a real blocker, but raw->10 alone was insufficient. P121/P122 global C48 bypasses did not solve cinematic. P123 call-replay hooks caused vanilla regression and are retired. P124 returns to native calls and only checkpoints post-gate reach.

## P125 design
Parent is compact P81 + direct P89. P125 installs six inline hooks total in this corrective family:
- P124 gate 0x77C474 (narrow register-only raw->10 overlay)
- P124 after-actor 0x77C498
- P124 after-peer 0x77C4AC
- P124 type9-zero 0x77C514
- P125 post-outer 0x77C5EC, after native BL 0x7EF098; replays native LDR W8,[X20,#0x50] and arms session latch only if native W0 !=0
- P125 cleanup request 0x7EB27C; replays native MOV W1,#125 and overlays W1=137 only when same custom semantic actor is action708, native outer returned success, and mature context E94=136/E98=135/E9C=0/BDA4=0/BDA8=0 is present

Native BL/BLR at 0x77C490,0x77C4A4,0x77C4B0,0x77C51C,0x77C5E8,0x7EB288 remain untouched. No direct session/state/action call from callbacks. No char281 branch.

## Decision
- no AFTER_ACTOR: actor C48 blocker
- AFTER_ACTOR but no AFTER_PEER: peer C48 blocker
- AFTER_PEER but no TYPE9_ZERO: type9/branch blocker
- TYPE9_ZERO but no POST_OUTER: pairing corridor 77C514..77C5E8 blocker
- POST_OUTER ret0: outer setup itself rejects
- POST_OUTER ret1 + CLEANUP session1 mature0: session exists but state context not mature; do not force137
- POST_OUTER ret1 + CLEANUP bridge1: P107 endpoint is reused only after native session setup and mature context; observe whether native710/cinematic lifecycle is now complete
- native710 without fallback: session/manager path repaired itself; fallback stays dormant
