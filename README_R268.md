# R268 Base Visual Child Gate Trace

Read-only diagnostic after R267 proved:

`typed mtobcharsel00+0x08 -> secondary+0x18 -> main+0x117E0D8`

all pass.

R268 traces only:

```text
0x117E0D8 visual list
 -> secondary+0x28
 -> list count +0x20 / entries +0x18
 -> 0x11A3E3C child gate
 -> 0x11A2444 child draw
```

Expected markers:

- `[NSC:R268] READY`
- `[NSC:R268] VISUAL_LIST_PRE`
- `[NSC:R268] VISUAL_ENTRY`
- `[NSC:R268] CHILD_GATE`
- `[NSC:R268] CHILD_DRAW`
- `[NSC:R268] VISUAL_LIST_POST`

Deploy with clean `main`, R263 `sound.cpk`, no external Tobi CPK, ID281 off.
