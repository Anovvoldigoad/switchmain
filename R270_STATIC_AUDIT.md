# R270 Static Audit — Matcher fallback key/type compare

R269/log44 proves the base-visual candidate source is linked correctly and the population method executes, but `main+0x11A2D4C(candidate, descriptor)` returns zero. The visual slot therefore remains NULL.

The matcher was statically recovered on clean Switch v1.70 `main`. In this target run `candidate+0x118+0x38` and `+0x40` are both NULL, so the primary string/hash branch is skipped. The exact fallback path is:

```asm
11A2E10  MOV X0,X20
11A2E14  LDR X8,[X8,#0x50]     ; descriptor vfunc+0x50
11A2E18  BLR X8
11A2E1C  MOV X20,X0            ; descriptor key/type record
11A2E20  LDR X0,[X19,#0x18]
11A2E28  LDR X8,[X0]
11A2E2C  LDR X8,[X8,#0x50]     ; candidate18 vfunc+0x50
11A2E30  BLR X8
11A2E34  LDRB W8,[X20,#4]      ; descriptor type
11A2E38  LDRB W9,[X0,#4]       ; candidate type
11A2E3C  CMP W8,W9
11A2E40  B.NE fail
11A2E44  LDR W8,[X20]          ; descriptor key
11A2E48  LDR W9,[X0]           ; candidate key
11A2E4C  CMP W8,W9
```

R270 installs one inline capture at `main+0x11A2E34`. At this exact point X20 already holds the descriptor record and X0 holds the candidate record. The tracer reads `{u32 key,u8 type}` from both records, logs equality, then exactly replays the overwritten native instruction `LDRB W8,[X20,#4]`. It does not call either vfunc again and does not alter IDs, paths, data, return values, game state, or `main` bytes.

Decision:
- `type_equal=0` -> exact type discriminator mismatch.
- `type_equal=1,key_equal=0` -> exact numeric key mismatch; then search/derive which side carries stale/native namespace identity.
- both equal while matcher returns zero -> re-audit a different matcher branch/control-flow assumption.
