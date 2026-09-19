NSC2Switch P56B — READ-ONLY CONTROL-BLOCK LOCATOR (Switch v1.70)
=================================================================

WHY P56A IS WITHDRAWN
P55A sampled action 74/77 only when Event236/Event121 callbacks happened. There
was no raw-input marker tying those samples to the user's XXA press. Therefore
74/77 cannot honestly be called the XXA->XA route. P56A setter-discovery was
based on that unsupported correlation and SHOULD NOT BE TESTED.

WHAT IS ACTUALLY SOURCE-PROVEN
UltimateStormAPI SC1.70 me_enable_control(actor, enemy, control) uses separate
control selectors. In the recovered source:
  selector 1 -> enable Ultimate Jutsu
  selector 2 -> enable Jutsus
Event236 custom traffic from Tobi repeatedly contains op14,p2=0,p3=1 and p3=2.
P50A intentionally shadows op14, so these enable requests currently do nothing.
This is a plausible upstream reason XXA can fall through to ordinary XA, but it
is NOT yet proven causal.

WHAT IS ALREADY DISPROVEN
Do NOT write actor+0x12A24. P40 hardware tested that historical PC->Switch
candidate and observed non-boolean values (e.g. selector1/UJ=58,
selector2/Jutsu=26). P41A therefore returned O14 to the safe shadow baseline.

P56B STRATEGY — NO GAMEPLAY WRITE
Keep the hardware-stable P50A five-trampoline core unchanged. Reuse existing
callbacks only:
  * Custom Event236 op14,p2=0,p3=1: snapshot when the mod requests UJ enable.
  * Vanilla PlayAction(700): snapshot a proven successful vanilla UJ entry.

For each snapshot, scan actor-relative bases 0x12800..0x12B20 in 4-byte steps.
At each base, score the exact PC source relative control-field geometry for
boolean values. The maximum mapped field is +0x58, so the scan cannot read past
actor+0x12B78, an independently recovered Switch actor-region boundary.

The logger emits the best eight candidates:
  [NSC:P56B] CONTROL_SNAPSHOT ...
  [NSC:P56B] CONTROL_CAND ... base=... bool=... ones=... uj=... jutsu=...

IMPORTANT
A high boolean score is a locator clue, not proof by itself. A convincing
candidate should recur at the SAME actor-relative base in vanilla and custom
snapshots and have semantically plausible fields. We will not write it until
hardware data establishes that.

ACTIVE TRAMPOLINES = 5 ONLY
  0x473190 CpkBind
  0x816300 Event236 compatibility
  0x766B8C PlayAction observation
  0x754A80 ConditionGetter
  0x8134F8 Event121 SELF compatibility

NO NEW HOOKS. NO CONTROL WRITES. NO CHAR281 FIX. NO 708->710.

EXPECTED READY
[NSC:P50A] READY ... installed_trampolines=5 ...
[NSC:P56B] READY inherited_p50=1 control_locator=1 added_trampolines=0 total_trampolines=5 writes=0 ...

TEST ORDER (ONE LOG)
1. Naruto vanilla: perform one successful UJ (XXA) once.
2. Start a fresh match with Tobi True Awakening.
3. Let battle initialize, then press XXA 2-3 times (it may still produce XA).
4. Close emulator and send the full log + build artifact.

DECISION RULE
- Same high-scoring base in VANILLA_PLAY700 and CUSTOM_O14_UJ_ENABLE -> inspect
  exact UJ/Jutsu fields and static xrefs before any write.
- No stable common base -> reject the contiguous PC-style control-block model
  for Switch and move to command/predicate xref tracing; do not force a field.
