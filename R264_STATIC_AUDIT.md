# R264 Static Audit — Secondary Preview Object / Draw Submit

## Log38 lock
- R263 preview remains empty.
- R263 visibly changes the parenthetical UI text to `()`, proving the replacement charsel is active, but not sufficient for preview.
- R252 still captures target `data/ui/max/crsel/c/mtobcharsel.xfbin` and the target remains in normal Wait state.

## Clean-main boundaries
- `main+0x549950` Wait::enter.
- `main+0x6EB554` secondary preview-object builder.
  - requires `model+0x90 != NULL`;
  - performs `main+0x1207B38` file-resource lookup;
  - performs `main+0x120A3D4` typed chunk lookup;
  - only after successful lookup/allocation eventually stores the created object at `model+0x98` (`STR X21,[X19,#0x98]` at main+0x6EB750).
- `main+0x54ADA0` character-select Draw callback.
  - loads state `self+0xB0` model;
  - calls `main+0x6ECBC0`;
  - `0x6ECBC0` returns `(model+0x98 != NULL)`;
  - if false, Draw returns without submit.
- if true and draw context is non-null, Draw tail-branches to `main+0x5B3AC`.

## R264 purpose
Read-only target-scoped proof of:
1. `model+0x98` pre/post Wait enter;
2. exact file lookup path/result nested inside `0x6EB554`;
3. exact typed chunk key/result nested inside `0x6EB554`;
4. Draw model/base90/secondary98;
5. whether target reaches the final draw submit boundary.

No path rewrite, return override, ID patch, state force, CPK bind, gameplay patch, or main patch.
