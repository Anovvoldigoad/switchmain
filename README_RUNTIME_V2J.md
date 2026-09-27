# NSC2Switch Runtime V2J — Switch-native Stage Post + D-pad Consumer Probe

Target: Storm Connections Switch v1.70 / original main.

V2J starts from the hardware-tested V2I runtime. V2I established three separate
results: generic opcode26 audio playback works; the requested custom stage ID is
accepted but the battle map remains visually mixed; and condition+Right charge
alone changes the D-pad/substitution-cell behavior but does not reproduce the
full advertised Izanagi protection.

## Audio — frozen PASS
V2I's generic opcode26 path is unchanged. It resolves the exact 160-entry NSC
SFX list and uses the statically proven Switch v1.70 actor vtable +0x1030 sound
contract. No new audio experiment is introduced in V2J.

## Stage — combine PC participant fix with Switch-native post transition
V2I already proved `STG_2TOB_UNI_LT` resolves and the live stage ID changes to
CRC `0x01D1CA7E`. The remaining failure is downstream visual/environment state.

Static Switch v1.70 code has a native stage-transition sequence:

- `main+0x48E358` -> `HandleStageChange(stage_id)`
- `main+0x48E360` -> `FixCharPosition(actor)`
- `main+0x48E364` -> `main+0x48E61C` post-stage/member sweep

V2I intentionally omitted the final Switch-native call while adding the PC
source requirement to fix both actor and enemy. V2J tests the previously
untested combination: HandleStageChange -> fix actor -> fix enemy -> native
post-stage sweep. Marker: `[NSC:V2J] STAGE2_SWITCH_NATIVE`.

## D-pad Right — read-only native consumer probe
V2I replays the source frame-13 activation core (`SW_MTOB_XH` + opcode17 Right
100.0f) with PL_ANM930 still suppressed. Hardware shows that this affects the
D-pad/substitution-cell behavior but is not yet full Izanagi protection.

PC source identifies actor+0xF30 as the D-pad-animation enable. Independently,
Switch v1.70 contains a native F30 consumer at `main+0x7E74A4`, inside the
resolved STATE137 controller family:

```
CMP W0,#1
B.NE ...
LDR W8,[X20,#0xF30]
CBZ W8,...
... vtable +0xBA8 ...
... vtable +0xBB8 ...
```

V2J installs one read-only inline probe at that LDR. The hook faithfully replays
`LDR W8,[X20,#0xF30]` into W8 and only logs actor identity, F30, Right charge,
E94/E98, and animation state. It does not alter any branch, return value, or
gameplay field. The location is derived from the uniquely resolved
STATE137_CONTROLLER anchor (`+0x5FC`) and fail-closed fingerprinted before hook
installation. Markers: `[NSC:V2J] DPAD_NATIVE_READY` and
`[NSC:V2J] DPAD_NATIVE_CONSUMER`.

The V2I activation-core A/B remains unchanged for this controlled comparison.
There is still no force-no-damage, force-visible, forced action710, or char281
gameplay branch.

## Locked hashes
Original/restore main SHA256:
`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

Reference P128 main is verifier-only; never deployed.
