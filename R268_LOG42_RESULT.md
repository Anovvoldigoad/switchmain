# R268 — Hardware Log42 Result / R267 Outcome

Date: 2026-10-06
Input: `uzuy_log(42).txt`

## Hardware locks from R267

- `R267_RUNTIME_INSTALL=HARD_PASS`
- `R267_TYPED_INNER08=HARD_PASS_NON_NULL`
- `R267_SECONDARY18_BIND=HARD_PASS_EQUAL_TO_TYPED_INNER08`
- `R267_BASE_MODEL_DRAW=HARD_PASS`
- `R267_BASE_VISUAL_DRAW_0x117E0D8=HARD_PASS_REPEATED`
- `R267_INNER_BINDING_AS_PREVIEW_BLOCKER=FALSIFIED`

Observed first target bind:

```text
INNER_BIND_PRE  typed_inner08=0x3b1d496e00 pre_inner18=0
INNER_BIND_POST typed_inner08=0x3b1d496e00 post_inner18=0x3b1d496e00 equal=1
```

Observed immediately afterward:

```text
BASE_DRAW_PRE inner18=0x3b1d496e00 id38=46
BASE_VISUAL_DRAW ... reached=1
BASE_DRAW_POST ... visual_calls=1
```

The same base visual call repeats every Draw frame.

## Frontier change

The preview remains visually empty even though the target reaches `main+0x117E0D8` repeatedly. Therefore the new frontier is downstream inside the visual-list/child-draw path executed by `0x117E0D8`.
