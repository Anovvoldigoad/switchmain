# R68 / P59A checkpoint

## Locked proven chain
- P58 runtime: Tobi two XXA attempts -> PlayAction(445) twice from main+0x7B4B2C -> 74/445/74 cycles.
- Naruto vanilla UJ -> PlayAction(700) at main+0x7E35E8 -> normal 700..740 progression.
- 0x7B4680 is a vtable+0xE40 virtual thunk; 0x7B468C is its base implementation.
- P58 wrong-jutsu callsite 0x7B4B2C is inside that base implementation.
- Base mode0 resolves literal 445 through vtable+0x1488 and later calls PlayAction(w21).

## P59A objective
Capture base-entry mode + caller provenance + current actor vtable+0xE40 target. Broaden the
existing PlayAction logger to all side0 calls so vanilla XA is visible.

## No gameplay hypothesis is promoted to root cause in P59A
Event236 op14/UJ-enable shadow remains a candidate only. P59A does not change it.
