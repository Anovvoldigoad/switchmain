NSC2Switch P38A — O14 ENABLE-CONTROL SHADOW CAUSAL A/B
======================================================

WHY
---
P37A proved O12 visibility is not the conditional victim-UJ cause:
Naruto slot1 and Isshiki still make Tobi disappear after UJ, Naruto Sage does not,
and StageMove remains functional. Fresh P37A runtime markers confirm VIS_SHADOW
actually executed, so the negative is valid.

P34A (all custom Event236 no-op) had victim-UJ normal, while P35/P36/P37A with
selected handlers live reintroduced the conditional failure. P38A therefore isolates
the next live handler relative to P37A: opcode 14 / me_enable_control.

ONLY NEW GAMEPLAY DELTA VS P37A
-------------------------------
O14 is now shadow/no-op and returns success:
  [NSC:P38A] CTRL14_SHADOW actor=<ptr> side=<n> char=<id> p2=<n> p3=<n>

O12 stays shadowed from P37A. StageMove and other P37A handlers are unchanged.
This makes P37A -> P38A a one-variable causal A/B.

DEPLOY AFTER CI BUILD
---------------------
1. Use restore/.../exefs/main from the P38A artifact as exefs/main.
2. Use compiled P38A subsdk9 as exefs/subsdk9.
3. Keep P33A Tobi_Switch.cpk Sorted=0 and current RomFS/params/charicon.

Startup marker must include:
  [NSC:P38A] READY ... vis12_shadow=1 ctrl14_shadow=1 ...

TEST
----
1. Tobi vs Naruto slot 1: let enemy UJ connect; check Tobi after cinematic.
2. Tobi vs Isshiki: let enemy UJ connect; check Tobi after cinematic.
3. Trigger Tobi StageMove once; it must remain functional.
4. Naruto Sage slot 5 is an optional PASS control.
5. Send the full fresh Uzuy log.

INTERPRETATION
--------------
- If Naruto slot1 + Isshiki no longer make Tobi disappear while StageMove remains PASS:
  O14 current Switch enable-control implementation is causally implicated.
- If disappearance remains unchanged:
  O14 is negative; next isolate O13 while preserving O12+O14 shadows.

Do not use awakening or Tobi's own Kamui as the pass/fail criterion for P38A.
Those remain separate unresolved targets.

P38A is diagnostic, not the final compatibility implementation.
