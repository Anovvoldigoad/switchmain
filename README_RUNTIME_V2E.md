# NSC2Switch Runtime V2E — D-Pad Right / Opcode17 Source-Parity Stage 1

Parent: hardware-PASS V2D original-main runtime architecture.

Original/restore main SHA256 (must remain deployed on disk):

`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

## Why this patch exists

Latest V2D hardware log proves the Right-DPad Izanagi sequence reaches:

- action 928
- Event236 opcode23 `SPTYPE_ACTION10` -> action 930
- condition `SW_MTOB_XH` executes
- Event236 opcode17 fires with `p2=0`, `p3=4`, `p4=100.0`

But V2D still explicitly shadows opcode17, so the real MovesetPlus D-pad charge write never occurs.

PC UltimateStormAPI source for SC 1.70 defines `me_change_dpad_charge` as four float fields at actor+0x12B88. Prior Switch layout work established the corresponding Switch block at actor+0x12B78 (PC->Switch -0x10 for this structure). Arrow 4 is Right D-pad, therefore the live Izanagi event must write `100.0f` to Switch actor+0x12B84.

## V2E change

Only Event236 opcode17 behavior changes:

- p2 0/1 selects self/enemy exactly like PC source;
- p3 0 writes all four D-pad charges;
- p3 1/2/3/4 writes Up/Down/Left/Right;
- the value is written exactly, including the real Tobi value 100.0;
- the obsolete experimental abs(value)<=16 rejection is NOT present;
- no char281 branch;
- opcode12 visibility shadow remains unchanged;
- opcode23 remains unchanged in this stage;
- UJ runtime corridor and original-main V2D architecture remain unchanged.

Expected marker for Tobi Right-DPad:

```text
[NSC:V2E] DPAD17_APPLY ... enemy=0 arrow=4 charge_bits=42c80000 ... base_off=0x12b78 source_parity=1
```

Expected `after` fourth float is `42c80000` (100.0f).

## Test

1. Confirm boot still reports V2D original-main runtime patch READY.
2. Naruto UJ once.
3. Tobi victim UJ once.
4. Tobi own UJ once.
5. Press Right D-pad once.
6. Observe whether Tobi remains visible / returns correctly.
7. Let the enemy hit Tobi repeatedly and check whether damage is prevented.
8. Observe substitution gauge recovery.
9. Save log before Left D-pad or restarting battle.

Decision:
- DPAD17 marker absent: event routing regression.
- marker present + field becomes100 + Izanagi works: opcode17 was the missing causal piece.
- marker present + field becomes100 but disappearance/no immunity remains: next target is opcode23 animation semantics (`SetActionImmediate` + `SetAnmDirect`) / SPTYPE_ACTION10 event behavior, not D-pad charge.
