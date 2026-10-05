# R268 Static Audit — Base Visual List / Child Gate

## Why R268 exists

R267 hardware proves the actual base-body visual call `main+0x117E0D8` is reached repeatedly with a non-NULL inner binding. R268 does not reopen charsel lookup, secondary construction, accessory submit, or Wait child-vector hypotheses.

## Exact `main+0x117E0D8` structure

```asm
117E0E0  LDR  X8,[secondary,#0x28]
117E0E4  CBZ  X8,return
117E0E8  LDRH W9,[X8,#0x20]       ; count
117E0EC  CBZ  W9,return
...
117E104  LDR  X8,[X8,#0x18]       ; entry array
117E108  LDR  X0,[X8,X20]         ; first ptr in 0x68-byte record
117E10C  CBZ  X0,next
117E110  BL   0x11A3E3C
...
117E120  ADD  X20,X20,#0x68
```

Thus the unresolved runtime values are:

- `secondary+0x28` visual-list pointer;
- `list+0x20` entry count;
- `list+0x18` entry array;
- first pointer in each `0x68`-byte record.

## Exact child gate `main+0x11A3E3C`

```asm
11A3E44  LDRB W8,[child,#0x2E4]
11A3E48  TBNZ W8,#2,continue
          RET

continue:
11A3E58  LDR X8,[child]
11A3E60  LDR X8,[X8,#0x30]
11A3E64  BLR X8
11A3E68  CBNZ W0,draw
11A3E6C  LDRB W8,[child,#0x125]
11A3E70  CBZ W8,skip-primary-draw

draw:
11A3E78  BL 0x11A2444
```

The function then optionally walks additional children using count `child+0x170` and an array at `child+0x1C0`, feeding them to `0x11A2444` as well.

## R268 decision tree

1. `list28=0` or `count20=0` -> base visual call is reached, but its visual-child list is empty.
2. entries exist but child pointers are zero -> visual records exist without drawable objects.
3. child exists and `child+0x2E4 bit2=0` -> exact disabled child gate.
4. bit2=1 but no `CHILD_DRAW` -> vcall `+0x30` returns false and `byte+0x125==0`, or equivalent child gate path.
5. `CHILD_DRAW` is reached -> frontier moves downstream of `main+0x11A2444`.

R268 is read-only and does not force any field, return, ID, path, CPK binding, or gameplay state.
