# R69 / P60A — Native UJ Control Port

## Locked P59 result
P59 hardware A/B with Kakashi vanilla and Tobi custom proved the divergence occurs before the action handler:
- Kakashi XA: e94=0x4D, mode0, PlayAction445.
- Kakashi UJ: e94=0x87, PlayAction700.
- Tobi XA and both Tobi XXA attempts: e94=0x4D, mode0, PlayAction445.

## Root-level binary finding
Switch v1.70 has a native indexed control array/API:
- getter main+0x7C6280
- enable setter main+0x7C65B0
- native control object is actor+0x228
- UJ router reads native selector 8 before selecting state 0x87.

The custom moveset emits Event236 op14 p2=0 p3=1 (MovesetPlus enable UJ control), but the inherited bridge shadows it and returns success without invoking the Switch-native API.

## P60A functional delta
Exactly one source semantic mapping is enabled:
`Event236 op14 p2=0 p3=1` -> `0x7C65B0(actor+0x228, 8)`.

P60A verifies exact getter/setter fingerprints before enabling the mapping. If either fingerprint mismatches, the mapping stays disabled and Event236 fails closed to shadow behavior.

P59 diagnostics remain active to prove the result. No action or state is forced.

## Acceptance test
1. Vanilla control character: XA then UJ; both must still work normally.
2. Tobi setup/True Awakening as in P59.
3. Tobi XA once: should remain ordinary jutsu / 445.
4. Tobi XXA once, then again: desired proof is P60 CTRL14_UJ_PORT after=1 and Tobi reaching PlayAction700/UJ progression instead of 445.
5. Regression: let a vanilla opponent UJ hit Tobi; after cinematic Tobi must remain visible and playable. Enemy visibility must remain normal.

Awakening is NOT claimed fixed by P60A. Its source/native selector mapping remains unproven and intentionally untouched.
