# NSC2Switch Runtime V2H — Safe Opcode23 + Stage/Audio Probe

Target: Storm Connections Switch v1.70 / original main.

V2H is a diagnostic rollback after V2G hardware disproved `main+0x766320` as a safe SetAnmDirect equivalent.

## Gameplay behavior
- Preserves V2D original-main resolver + exact 30-word runtime patch architecture.
- Restores V2F-safe opcode23 behavior: `SetActionImmediate(param3)` + PL_ANM lookup, but no call to `0x766320` and no `PlayAction(index)` for opcode23.
- Keeps opcode17 source-parity D-pad charge handling.
- No global visibility/no-damage hack and no char281 gameplay branch.

## New diagnostics
- `STAGE2_ENTER/STAGE2_FAIL/STAGE2_DONE` around opcode2 stage switching, including requested stage CRC and stage ID before/after the specific handler.
- `OP26_PROBE` for MovesetPlus generic sound events. It resolves the source NSC 1.70 SFX index and snapshots Switch actor vtable slots around PC's historical +0x1020 location, but performs no playback.

## Locked hashes
Original/restore main SHA256:
`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

Reference P128 main is verifier-only; never deployed.
