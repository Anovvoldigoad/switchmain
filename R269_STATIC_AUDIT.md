# R269 STATIC AUDIT — Base Visual Population / Descriptor Match

## Supersedes
R268 proved the base visual list exists and has `count20=1`, but `entries[0]` remains NULL for the target during the entire hover. Therefore `0x11A3E3C` child gate and `0x11A2444` child draw are not the current boundary.

## Exact recovered chain
Within the target secondary-object build:

1. `main+0x6EB728` loads `model+0x90`.
2. `main+0x6EB730` calls `main+0x117D390`.
3. `main+0x117D390` is exactly:
   `STR X1,[X0,#0x188]; RET`
   Therefore `secondary+0x188 = model+0x90`.
4. The secondary typed-load path later reaches the visual population method `main+0x117BA00`.
5. `0x117BA00` reads:
   - typed visual count from `typed+0xB0`;
   - candidate source from `secondary+0x188`;
   - visual list from `secondary+0x28`;
   - entries array from `list+0x18`;
   - descriptor table from `typed+0xA8`.
6. For each visual index, it calls:
   `main+0x11A2D4C(candidate, descriptor)`.
7. Only when that matcher returns non-zero does it execute:
   `STR candidate,[entry]` at `main+0x117BB7C`.

## Runtime implication from log43
R268 observed:
- visual list pointer NON-NULL;
- `count20=1`;
- entries array NON-NULL;
- entry 0 pointer NULL in every sampled frame;
- no real child-gate or child-draw callback.

Therefore the first unresolved base-preview boundary is now the population step, not child visibility.

## R269 diagnostic
Read-only hooks:
- `0x117D390` source188 link;
- `0x117BA00` population method;
- `0x11A2D4C` candidate/descriptor matcher;
plus the already-proven target capture/build/draw/list observation hooks.

Decision tree:
- `source188=0` -> base90 link missing.
- `source188!=0`, matcher returns 0 -> exact charsel/base-model descriptor mismatch.
- matcher returns 1 but `child0_post=0` -> post-match fill/assignment blocker.
- `child0_post!=0` but R268 visual-list observation later sees NULL -> later clear/teardown after population.

No game data, IDs, paths, returns, or state values are modified.
