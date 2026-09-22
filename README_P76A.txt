NSC P76A — READ-ONLY UJ FORK RUNTIME PROBE

BASELINE
P76A preserves the complete P67A behavior first.

P67A remains responsible for:
- P50 victim-UJ safety shadows
- semantic MovesetPlus selector1 state
- selector1 consumer diagnostics
- existing P57/P59 diagnostics
- source-parity main prerequisite

P76A CHANGE
Two normal function-entry trampolines are added for diagnostics only.

ALT corridor:
  target main+0x8B2D04
  active caller return main+0x7F4598

UJ corridor:
  target main+0x8B2B70
  active caller return main+0x7F4648

Both targets were ABI-audited as:
  uint32_t(void* actor)

Both probes:
- call Orig(actor)
- preserve the native return exactly
- write no gameplay fields
- log actor identity
- log semantic selector1 state
- log E94/E9C before/after
- filter the active classifier using exact caller return

PURPOSE
Prove where vanilla UJ and Tobi XXA diverge before any functional fix.

PRIMARY RUNTIME HYPOTHESIS

Vanilla UJ:
  -> UJ_CORRIDOR

Tobi XXA:
  -> ALT_CORRIDOR

If both reach UJ_CORRIDOR, continue inside the UJ corridor rather than
modifying the early +0x1288 fork.

NO
- char281 gameplay branch
- force state87
- force action700
- selector8 mapping
- F58 forcing
- inline BLR replacement
- raw Event236 restore

MINIMUM TEST
1. Vanilla XA sanity
2. Vanilla UJ once
3. Tobi XA sanity
4. Tobi XXA once
5. Verify victim safety has not regressed

Build target:
Nintendo Switch NSC 1.70
Build ID:
48ece454b61412b9fb46fab2be3f5ef7b2804f39
