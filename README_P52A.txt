NSC2Switch P52A — PRE-UJ DECISION PROBE

BASELINE
- P50A functional condition-compat core.
- P51A speculative main+0x7F2A9C NOP is REJECTED and NOT present.
- Deploy main SHA256 remains P50A: 8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be

WHY P52A EXISTS
Hardware P51A result: Tobi true awakening is active, but awakened UJ still cannot start.
The log contains Naruto PlayAction 700->707->710->...->740, while Tobi has no PlayAction(700).
Therefore the current failure is upstream of the cinematic/action chain.

STATICALLY PROVEN SWITCH v1.70 BOUNDARIES
1. main+0x488958: actor/mode wrapper that calls main+0x7E3534.
2. main+0x7E3534: UJ-start state core; MODE 0 executes PlayAction(700) at main+0x7E35E8.
3. main+0x646190: CtrlAct_PL_ACT_NORMAL_SPTYPE_SPSKILL controller.
   Exact xref to warning string occurs at 0x64678C. The controller routes native special-type
   actions including 921 and 930; 930 corresponds to SPTYPE_ACTION10 observed in Tobi logs.
4. Existing Ougi caller/core boundaries are also traced: 0x488BAC -> 0x7E0F58.

P52A ADDED TRAMPOLINES — READ ONLY
- UJ_WRAPPER      0x488958
- UJ_STATE        0x7E3534
- SPTYPE_CTRL     0x646190
- OUGI_CALLER     0x488BAC
- OUGI_CORE       0x7E0F58

Inherited P50A trampolines remain:
- CPK bind, Event236, PlayAction, ConditionGetter, Event121.
Total active trampolines: 10. Event121 is NOT double-hooked.

NO FUNCTIONAL PATCH IN P52A
- No forced UJ result.
- No 707/708 rewrite.
- No main NOP.
- No actor state write.
- No char 281 / donor 57 / COND_2DNZ branch.

TEST ORDER
1. Naruto normal UJ once.
2. Tobi before awakening: try UJ once (if the moveset allows it).
3. Activate Tobi true awakening.
4. Try awakened UJ 2-3 times.
5. Save the full Uzuy log and send it.

DECISION
- Naruto hits UJ_WRAPPER/UJ_STATE mode0 but awakened Tobi does not:
  failure is upstream selector/input eligibility. Compare SPTYPE_CTRL traces.
- Tobi hits UJ_WRAPPER but not UJ_STATE:
  wrapper gate is the boundary.
- Tobi hits UJ_STATE mode0 but no PlayAction700:
  state-core internal preconditions are the boundary.
- Tobi reaches PlayAction700:
  then return to 700/707/708/710 progression analysis.

The final fix will remain data-driven from ougiAwakeningParam, not character-specific.
