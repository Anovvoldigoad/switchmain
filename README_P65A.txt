NSC P65A — SOURCE-PARITY ACTIVE UJ BRIDGE

Parent:
P64F semantic selector1 state + P50 victim-safe core.

Functional changes:
1. P64 0x7ABE9C consumer is NOT installed.
2. Event236 selector1 semantic state remains active.
3. F58 main+0x7D3138 is functionally overlaid only when:
   - native result is false,
   - caller LR is exactly main+0x7F46B8,
   - selector1 semantic is enabled for the same actor.
4. Paired main:
   main+0x7F2A9C
   BD001FE0 -> D503201F
   STR S0,[SP,#0x1C] -> NOP.

No char281 branch.
No force action700.
No force state0x87.
No selector8 mapping.
No raw native Event236 restoration.
No old 0x7E1404 wrapper.

Hardware gate:
- Tobi XXA
- vanilla UJ control
- Tobi victim of enemy UJ
