# R73 / P64F checkpoint

P64F is the first post-P63 functional build.

Root evidence carried forward:
- Tobi's MovesetPlus Event236 explicitly requests selector1 enable.
- UltimateStormAPI source defines selector1 as Ultimate Jutsu control.
- P63 current runtime resolves Tobi XA and XXA to state 0x4D / action445.
- Tobi does not reach the previously-probed F58 path on the failing XXA attempt.
- P40/P62 eliminate blind actor+0x12A24 writes and global selector8 override.

New static discovery:
- Switch main+0x7ABE9C queries native control getter selector1 at 0x7ABF30.
- That helper is called directly from the UJ router at C76C0/C76EC/C78D0.

P64F experiment:
- retain selector1 semantic per actor from Event236 op14/op15;
- promote only the 0x7ABE9C predicate at those exact UJ-router callers;
- preserve native true and every downstream native route;
- no character-specific logic and no forced state/action.

Hardware result is required before this becomes a trusted compatibility layer.
