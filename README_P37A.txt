NSC2Switch P37A — O12 VISIBILITY SHADOW CAUSAL A/B
===================================================

BASELINE
- Inherits P36/P35A generic Event236 runtime and P33A Sorted=0 CPK requirement.
- Restore main must remain SHA256:
  2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
- Vanilla charID <= 280 still follows native Event236 unchanged.
- Generic custom IDs 281..0xFFF still enter MovesetPlus dispatcher.

WHY P37A
P34A no-oped all custom Event236 operations and enemy-UJ victim restore became normal.
P35A/P36 re-enabled a selected generic MovesetPlus core and conditional Tobi disappearance
returned after some enemy UJs. P36 proved the failing UJs do NOT traverse the generic
StageMove chain (HandleStageChange/FixCharPosition/PostStage), and custom actor pointers
continue after long cinematic gaps. Therefore the next narrow causal variable is the active
visibility handler O12.

ONE GAMEPLAY DELTA VS P36
Event236 opcode 12 (me_SetPlayerVisibility) is SHADOWED / NO-OP for custom actors only.
Everything else from P36 stays live:
- O2 StageMove
- O3 change_skill
- O4 change_speed
- O8 walk_speed
- O13 dpad animation
- O14 enable_control
- O15 historical safe no-op
- O22 play_pl_anm
- O23 play_action
- all other unproven custom opcodes stay shadow/no-op
- vanilla Event236 remains exact native behavior

P37A never calls native ME_ENEMY_DISP_OFF for a valid custom MovesetPlus opcode.
No Tobi/281 gameplay hardcode is used; 281 is only the first generic custom-ID boundary.

NEW MARKER
[NSC:P37A] VIS_SHADOW actor=<ptr> side=<n> char=<id> p2=<value>

P36 lifecycle hooks remain read-only and are retained for correlation:
[NSC:P37A] STAGE_HANDLE ...
[NSC:P37A] FIX_CHAR ...
[NSC:P37A] POST_STAGE ...
[NSC:P37A] EVT235_SHOW ...
[NSC:P37A] EVT236 ...

DEPLOY AFTER CI
1. Use restore/main from the P37A artifact as exefs/main.
2. Use compiled P37A subsdk9 as exefs/subsdk9.
3. Keep P33A Tobi_Switch.cpk Sorted=0 and the current params/charicon/RomFS.

MINIMUM HARDWARE TEST
A. Tobi vs Naruto slot 1: let Naruto UJ connect; wait until cinematic ends.
B. Tobi vs Isshiki: let Isshiki UJ connect; wait until cinematic ends.
C. Quick StageMove positive control once.
D. Optional Naruto Sage slot 5 control.
Then stop emulation and send the full fresh Uzuy log.

DECISION
- If Tobi no longer disappears after Naruto slot1 / Isshiki while StageMove still works:
    O12 implementation is a necessary cause. Do NOT keep O12 as final no-op; reverse/port
    the exact Switch visibility semantics and target/state contract next.
- If disappearance is unchanged:
    reject O12 as sufficient cause and isolate O14 enable_control next.
- Kamui and awakening are NOT the primary pass/fail criteria for this A/B.

P37A IS A CAUSAL DIAGNOSTIC BUILD, NOT THE FINAL FIX.
