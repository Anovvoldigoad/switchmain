# NSC2Switch Master Checkpoint — R132 / P118A

## Locked target
- Game: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pinned commit: `229bbd6`
- Custom Tobi: generated char281; solution must remain generic/data-driven.

## Preserved functional baseline
- P50 victim-safe Event236 shadows remain required.
- P89 generic semantic/membership admission bridge remains required.
- Action708 is legitimate and must not be suppressed.
- No state/action/session forcing.

## P116 locked result
Successful vanilla creates cinematic session through `main+0x7EF098`; custom Tobi executes 700->707->708 but never calls `0x7EF098`. Therefore type9/type10 session creation and manager logic are downstream symptoms, not root.

## P117 decisive result (correct runtime log)
Correct P117 runtime loaded subsdk9 Build ID `A45CD9C942A8D8F9741FCA6D9AA78B3A2819818E`, READY probe_ok=1.

At successful vanilla char70 action707:
- P117 EVENT raw_type=10 / norm_type=10 / type10_11=1
- event mask48=0x4000
- vanilla later reaches state137/action710.

At custom Tobi char281 action707 before native 707->708:
- P117 EVENT raw_type=15 / norm_type=14 / mask48=0x300
- then P117 EVENT raw_type=24 / norm_type=24 / mask48=0x2000004e00
- zero raw type10/11 in the custom UJ window.
- action708 remains generated naturally by caller 0x7725D0.

Conclusion: the missing cinematic admission begins in the action-event stream upstream of session creation. Do not reopen victim125/126, type9 blocker, type10 creator, manager137, or force710.

## Static event dispatcher proof
Bucket5 dispatcher entry `main+0x77B560`:
- actor current event index: halfword `[actor+0xB9E4]`
- `0x77B590 -> main+0x3F4B00` event-record lookup
- `0x77B5A8 -> main+0x3F4BC0`
- event record raw type at +0x50
- `0x77C474..0x77C480`: `(raw_type & ~1) == 10` gates cinematic bucket5
- `0x77C5E8 -> main+0x7EF098`

`main+0x3F4B00` is a bounds-checked pure lookup:
- validates signed/nonnegative index and count
- event records base at container+0x48
- stride exactly 0x60
- returns `base + index*0x60` or nullptr.

## P118A purpose
P118A reuses the known boot-safe P117 boundary at `main+0x3F4BC0` and adds a read-only event-table neighborhood census:
- derives exact global event index from record pointer and lookup(0)
- logs raw event types index -4..+4
- scans +/-32 for nearest type10/11
- preserves native Orig exactly once
- no event cursor write, no branch patch, no session/state/action write.

Decision after next run:
1. Custom event has no type10/11 within +/-32: local loaded event block lacks cinematic trigger -> back-slice action707 event-block/data selection.
2. Type10/11 exists nearby but is not dispatched: cursor/index selection is wrong -> trace producer of actor+0xB9E4.

## Retired directions
- P111/P112 victim125/126 as universal root.
- Direct state remaps 39->125, 121->126, 125->136/137.
- Direct 0x7DE948 / PlayAction12 replay.
- B968 root / forced manager creation.
- P114 type9 as blocker.
- P115A multi-inline hooks (boot unsafe).
- P115B bucket5 single-gate as universal model.
- P116 session outer as root (proved missing upstream).
- P117 event-type presence question is closed: vanilla has type10, custom lacks it.
