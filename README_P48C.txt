NSC2Switch P48C — FUNCTIONAL CORE + LOW-PERTURBATION 707/708 DECISION PROBE
Target: Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
Known target Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39

WHY P48C EXISTS
P48B booted, but it regressed Tobi gameplay: the victim/opponent could disappear again.
The cause is architectural, not a newly proven 708 result. P48B removed the P47 Event236
compatibility dispatcher while trying to reduce trampoline count. Event236 is NOT merely a
logger: for custom character IDs (>280) it shadows unsafe visibility/control extension opcodes
(O12/O14/O15/O17/O18) and prevents them from falling into the native ME_ENEMY_DISP_OFF path.

P48C restores ONLY that proven behavioral core and keeps the new decision probe minimal.

ACTIVE HOOKS — EXACTLY 4
  0x473190  CpkBind       : bind Tobi_Switch.cpk fixture
  0x816300  Event236      : generic custom-character compatibility dispatcher; restores
                            VIS/CTRL shadows from the working P47 baseline
  0x766B8C  PlayAction    : UJ range 700..740 only; return + pre/post current action
  0x768E84  ActionLookup  : UJ range 700..740 only; requested index + pointer/null result

NOT ACTIVE
Older file-load, lifecycle, stage, Event13/Event121, Ougi-finish, ActionGate, ActionRemap and
other diagnostic hooks remain source-only and consume zero trampolines.

IMPORTANT DIFFERENCE FROM P48B
P48B READY reported installed_trampolines=3 and did NOT install Event236.
P48C MUST report:
  [NSC:P48C] READY cpk=1 event236=1 decision=1 installed_trampolines=4 ...

LOW-PERTURBATION RULE
PlayAction and ActionLookup immediately call Orig() for ordinary indices. Extra identity/state
reads and logging are performed only for action indices 700..740. This avoids the thousands of
hot-path ACTION_LOOKUP log records produced by P48B during normal battle.

FIRST TEST — DO NOT START WITH UJ
1. Remove/replace P48B subsdk9 with P48C only.
2. Boot.
3. Confirm READY line says event236=1 and installed_trampolines=4.
4. Pick Tobi and enter battle.
5. BEFORE using Ultimate Jutsu, verify the opponent remains visible/hittable during normal combat.
6. Only if normal combat is restored, use Tobi UJ once.
7. Then run one working vanilla UJ control and save both full logs.

EXPECTED COMPATIBILITY LOGS FOR CUSTOM CHARACTER EVENTS
When relevant, custom Tobi events may show lines such as:
  VIS_SHADOW
  CTRL14_SHADOW
  OP15_SHADOW
  OP17_SHADOW
  OP18_SHADOW
These are intentional functional compatibility behavior inherited from P47.

DECISION QUESTION AFTER GAMEPLAY IS STABLE
Compare ACTION_LOOKUP index=708 for Tobi vs a working vanilla control. Do not infer anything
from P48B's Tobi capture because gameplay had already regressed before the decisive UJ path.

DO NOT
- Do not use P48B for Tobi conclusions.
- Do not patch 708->710.
- Do not hardcode charID 281.
- Do not remove Event236 while testing custom character behavior.
