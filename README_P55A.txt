NSC2Switch P55A — ZERO-EXTRA-HOOK ACTION STATE SAMPLER (Switch v1.70)
==================================================================

WHY
P54A hardware capture booted correctly with 7 trampolines, but neither direct
owner candidate (0x2A472C/action98 nor 0x2A51B8/action100) executed at all.
The visible Tobi awakened jutsu also produced no relevant PlayAction record.
Those two direct-owner candidates are therefore eliminated for this path.

P55A STRATEGY
Return to the hardware-proven P50A functional core (5 trampolines) and sample
actor state from callbacks that are already firing during Tobi True Awakening:
Event236 and Event121 SELF. No new hook is added.

STATE FIELDS
- actor+4712 current action
- E60 / E94 / E9C / EA0
- skill slots E68 / E6C / E70

NEW LOGS
  [NSC:P55A] STATE236 ...
  [NSC:P55A] SKILL_WRITE ...
  [NSC:P55A] STATE121 ...
  [NSC:P55A] ACTION_ROUTE ...

ACTIVE HOOKS = 5 ONLY
  0x473190 CpkBind
  0x816300 Event236 compatibility
  0x766B8C PlayAction observation
  0x754A80 ConditionGetter
  0x8134F8 Event121 SELF compatibility

NO GAMEPLAY PATCH
No char 281 branch, no donor 57, no forced UJ, no input rewrite, no A33C60
NOP, no direct action-owner hooks, no 708->710 rewrite.

EXPECTED READY
[NSC:P50A] READY ... installed_trampolines=5 ...
[NSC:P55A] READY inherited_p50=1 state_sampler=1 added_trampolines=0 total_trampolines=5 ...

TEST
1. Fresh battle with Tobi True Awakening.
2. Press XXA 2-3 times until the unwanted XA jutsu is visibly produced.
3. Do not deliberately press standalone XA during the capture.
4. Send the complete Uzuy log.

DECISION
The action value carried by STATE121/STATE236 during the visible jutsu becomes
the next exact owner/selector target. This avoids another guessed action ID.
