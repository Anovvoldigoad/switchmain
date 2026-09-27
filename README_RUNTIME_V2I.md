# NSC2Switch Runtime V2I — Izanagi Activation-Core A/B + Stage/Audio Parity

Target: Storm Connections Switch v1.70 / original main.

V2I starts from the hardware-safe V2H opcode23 rollback. It does not call the
problematic full PL_ANM930 path, so the V2G disappearance route stays suppressed.

## D-Pad Right controlled A/B
Hardware V2H proved that Right D-Pad reaches opcode23 but never reaches source
Event236 opcode17 Right=100, so long-lived Izanagi protection is not armed.
The decoded source `PL_ANM_SPTYPE_ACTION10` has two critical frame-13 events:
- Event121 SELF `SW_MTOB_XH`
- Event236 opcode17 `(enemy=0, arrow=4, charge=100.0f)`

V2I keeps the full animation suppressed, but for the exact diagnostic fixture
`action_param=77` + `SPTYPE_ACTION10` it replays only those two source-proven
activation events. Marker: `[NSC:V2I] IZANAGI_CORE_AB`. This is an A/B proof,
not the final generic opcode23 implementation. There is still no char281 branch,
no global no-damage write, and no force-visible write.

## Stage parity correction
V2H hardware proved `STG_2TOB_UNI_LT` resolves and the live stage ID changes to
its CRC. The remaining Switch handler differed from PC source in two ways. V2I
now matches PC `me_test_switch_stage`: after `HandleStageChange(stage_id)` it
fixes both actor and enemy positions and does NOT make the extra PostStage call.
Marker: `[NSC:V2I] STAGE2_PARITY`.

## Opcode26 generic SFX playback
V2H resolved the actor vtable slots. Static Switch v1.70 code at
`main+0x813D88` proves native sound events call actor vtable `+0x1030` as:
`fn(actor, event_sound_id + 0x7000, 0)`.
V2I uses the same ABI for MovesetPlus opcode26 after resolving the exact 160-entry
NSC SFX list. Marker: `[NSC:V2I] OP26_PLAY`. This addresses generic UJ SFX;
character-specific Event150/ACB voice registration remains a separate frontier.

## Locked hashes
Original/restore main SHA256:
`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

Reference P128 main is verifier-only; never deployed.
