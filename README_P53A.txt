NSC P53A — XXA INPUT-PROMOTION / ACTION-ROUTE PROBE

PURPOSE
The hardware symptom is now precise: Ultimate Jutsu is XXA, ordinary jutsu is XA,
and the custom true-awakened character executes ordinary jutsu even when XXA is pressed.
P52A proved vanilla Naruto reaches UJ_STATE -> PlayAction(700), while the custom actor never
reaches the five P52 pre-UJ probes.

P53A therefore moves upstream without adding trampoline pressure.

ACTIVE RUNTIME
P53A returns to the hardware-proven P50A core only:
  CpkBind + Event236 + PlayAction + ConditionGetter + Event121 = 5 trampolines.
P52A's five read-only pre-UJ hooks are NOT installed.

The existing PlayAction hook is widened to observe only:
  84       = ordinary jutsu / CtrlAct_PL_ACT_SKILL mode-0 route
  930      = SPTYPE_ACTION10 diagnostic route
  700..740 = UJ/cinematic route
Everything else goes directly to Orig(). No action/state/return value is modified.

STATIC PROOF FOR ACTION 84
SC 1.70 main at 0x2A4514 is the CtrlAct_PL_ACT_SKILL handler. Its mode-0 path executes:
  0x2A4550 MOV W1,#84
  0x2A456C BL  0x766B8C (PlayAction)
The same handler references the native debug string "[CtrlAct_PL_ACT_SKILL]: ...".

TEST — KEEP IT CLEAN
1. Boot and confirm both READY lines:
   [NSC:P50A] READY ... installed_trampolines=5
   [NSC:P53A] READY ... total_trampolines=5
2. Vanilla control (Naruto normal): press XXA exactly once.
3. Custom true-awakened character: press XXA exactly once.
4. Do not press XA separately during those two samples.
5. Save the full Uzuy log and run:
   python analyze_p53a_log.py uzuy_log.txt

INTERPRETATION
- custom JUTSU84 after XXA = second-X/UJ promotion was rejected upstream and A became normal jutsu.
- custom UJ:700 = UJ command was promoted correctly; investigate downstream cinematic path instead.
- custom SPTYPE930 but no UJ:700 = special-type state consumed the command upstream.
- no custom route = failure is before PlayAction; use the full log/timing for the next boundary.

IMPORTANT SOURCE-PARITY FINDING
PC UltimateStormAPI's awakening-UJ support has TWO simultaneous parts:
  1) OugiAwakening membership wrapper at game+A20C00;
  2) v1.70 NOP at game+A33C60.
Earlier Switch experiments tested the gate and NOP separately. P53A does not combine them yet;
it is the minimal route proof before a combined source-equivalent P53B.

GENERIC REQUIREMENT
No Tobi/281/Danzo57/COND_2DNZ conditional is added to gameplay source.
Future final membership logic must be generated from ougiAwakeningParam data.
