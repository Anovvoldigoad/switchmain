# R70 CHECKPOINT — P61A UJ Eligibility Gate Compatibility

## Locked hardware facts
- P59: Kakashi XA -> state0x4D/mode0/445; Kakashi UJ -> state0x87/700.
- P59: Tobi XA and both XXA attempts collapsed to state0x4D/mode0/445.
- P60: native selector8 was enabled successfully 62 times (0->1), but custom
  PlayAction700 remained zero. Selector8-only root hypothesis is rejected.
- Latest victim-UJ hardware run restored side1 char281 to action74 and user confirms
  no disappearance regression.

## New root boundary
Native UJ router uses vtable+0xF58 BEFORE selector8/state0x87:
`main+0xC7870 BLR F58`, LR=`main+0xC7874`.
Both Kakashi and Tobi resolve F58 to `main+0x7D3138`.

## P61 functional delta
One extra trampoline at `main+0x7D3138`.
A native false is overridden only for a generic custom actor explicitly marked by
source Event236 `op14,p2=0,p3=1`, exact F58 mode0, exact router LR 0xC7874, and
successful native selector8 refresh. Vanilla and all other F58 callers retain native behavior.

## Success criterion
Hardware must show:
1. `[NSC:P61A] UJ_GATE_COMPAT ... override=1 caller_off=0xc7874`
2. later `[NSC:P59A] PLAY_CALL ... char=281 index=700`
3. XA remains ordinary-jutsu path, and victim-UJ remains visible/playable.
