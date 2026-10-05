# R269 LOG43 RESULT

Input: `uzuy_log(43).txt`

## Runtime
- R268 installed read-only.
- Target base model reaches the base visual list path.
- `secondary+0x28` is NON-NULL.
- list `count20` is exactly 1 on all 96 sampled frames.
- `list+0x18` entries pointer is NON-NULL and stable.
- visual entry 0 is NULL on all 96 sampled frames.
- every sampled `VISUAL_LIST_POST` reports `child_gate_delta=0 child_draw_delta=0`.
- no actual target `CHILD_GATE seq=` or `CHILD_DRAW seq=` callback was reached.

## Locks
`R268_VISUAL_LIST=HARD_PASS_NON_NULL`
`R268_VISUAL_LIST_COUNT20=HARD_PASS_1`
`R268_VISUAL_ENTRY0=HARD_FAIL_NULL_STABLE`
`R268_CHILD_GATE_REACHED=NO`
`R268_CHILD_DRAW_REACHED=NO`
`R268_CHILD_BIT2_AS_CURRENT_BLOCKER=FALSIFIED_NOT_REACHED`

## New frontier
Static recovery proves visual entry population occurs at `main+0x117BA00`, sourced from `secondary+0x188` and gated by `main+0x11A2D4C(candidate, descriptor)` before the candidate pointer is stored at `main+0x117BB7C`.

`CURRENT_FRONTIER=BASE_VISUAL_ENTRY_POPULATION_MATCH`
`NEXT=R269_READONLY_SOURCE188_POPULATE_MATCH_TRACE`
