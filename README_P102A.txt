NSC2Switch P102A — Exact Fallback74 Suppression Candidate
Target: Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39

Purpose
-------
P102A tests the exact fallback that log45 proved occurs after custom Kamui absorption:
current action708 -> PlayAction74 from main+0x798F30 (runtime LR main+0x798F34), while the UJ control lock remains BDA4=1.

P102A reuses the already-installed P50 PlayAction hook. It adds ZERO new trampolines.
It does NOT force 710, 708, E94, E9C, BDA4, BDA8, BDC8, or EA4.
It does NOT hardcode char281.

Functional gate
---------------
Suppress native PlayAction74 only when ALL match:
- runtime caller return = main+0x798F34 (callsite main+0x798F30)
- requested action = 74
- current action = 708
- semantic UJ latch = true
- actor char ID is in generated OugiAwakening membership
- E98 = 63
- E9C = 0
- BDA4 = 1
- BDC8 = 0

Suppression returns 1, matching the observed native PlayAction74 success value, and lets the caller continue.
The gate is bounded to 16 matching calls per UJ; after that it fails open to native behavior.
Count resets on a new PlayAction700 and when the semantic UJ latch is newly enabled/disabled.

Expected decisive result
------------------------
GOOD:
  [NSC:P102A] HOLD74 ...
  followed by PlayAction710 / HANDOFF from caller_off=0x7e6ec8 and cinematic.

FAIL-OPEN:
  repeated HOLD74 reaches count 16, then [NSC:P102A] FAILOPEN74 and native 74 resumes.

WRONG ROOT:
  HOLD74 occurs, but no 710 and a different transition/fallback takes over before fail-open.

Test
----
1. Boot and confirm [NSC:P102A] READY ... probe=1.
2. Use Tobi custom UJ and let Kamui absorb the enemy.
3. Check whether cinematic starts and whether Tobi regains control afterward.
4. Upload the full emulator log and compiled artifact.

Do not combine with P101A. P101 state125 guard is intentionally absent.
