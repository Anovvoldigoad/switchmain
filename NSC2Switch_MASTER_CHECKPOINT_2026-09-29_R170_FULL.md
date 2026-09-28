# NSC2Switch MASTER CHECKPOINT — R170
Date: 2026-09-29

## Locked target
- Game: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- original main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin: `229bbd6`

## Frozen PASS items
- P128 custom UJ admission/session hit-path foundation remains unchanged.
- R164 StageInfo/CPK fix is hardware PASS (`STG_2TOB_UNI_LT found=1`) and remains frozen.
- Icon remains frozen/solved.
- Voice investigation is intentionally paused.

## Why R169 is retired
R169 successfully forced a stuck custom UJ action707 through a direct animation `707->77->74` release. That is useful evidence but not a root fix. Historical hardware/checkpoints prove the custom native fallback previously progressed `707->708->125->261->74`. Earlier P101/P102 work also proved movement recovery can occur independently from proper UJ/cinematic lifecycle recovery. Therefore "can move" is not sufficient evidence that the UJ state machine is correct.

## R170 exact native boundary
Static Switch v1.70 disassembly proves:
- `main+0x7E48C4`: query current action.
- action707 branch reaches `main+0x7E48E4: BL main+0x769A4C`.
- caller return = `main+0x7E48E8`.
- gate return zero branches away, leaving 707.
- gate return nonzero performs `lookup(708)` at `main+0x768E84`.
- successful lookup dispatches action708 through actor vslot `+0xF98`.

Therefore the root discriminator for a genuine whiff loop is the native completion gate at `main+0x769A4C`.

## Gate internals proven statically
`main+0x769A4C` returns zero when any relevant blocker remains:
1. no actor+0x218 animation object;
2. animation flag blocker: `anim+0x50 != 0` and `anim+0x70 bit0 == 1`;
3. actor+0x1264 nonzero;
4. final timing predicate false.

Final timing reads:
- duration scalar from `anim+0x80`;
- current from `anim+0x74`;
- end from `anim+0x78`;
- global tick numerator/divisor;
then tests `current + scaled_duration >= end`.

## R170 design
R170 removes the R169 action mutation entirely and adds exactly one read-only trampoline at `main+0x769A4C`.
It logs only:
- side0;
- custom character ID >280 and <0x1000;
- action707;
- exact caller return `main+0x7E48E8`.

The hook calls `Orig(actor)` once and returns the native value unchanged. It logs the native return plus the fields needed to classify the zero-return reason as `no_anim`, `anim_flag70`, `actor1264`, `timing`, or `pass`.

No force708. No force710. No direct77/74. No game-memory write.

## Perturbation reduction
R170 omits the V2M passive stage observer trampolines because R164 stage behavior is already hardware-PASS. V2N/V2P proof markers remain. Voice probes remain disabled. This keeps the hardware run focused on the 707 gate and reduces logging/hook pressure.

## Hardware test
1. Keep R164 fixed CPK unchanged.
2. Install R170 runtime.
3. Fresh boot.
4. Trigger one Tobi UJ and intentionally miss.
5. Do not touch movement for 8–10 seconds.
6. Exit and upload the complete Uzuy log.

Primary marker:
`[NSC:R170] UJ707_GATE ...`

Decision:
- repeated `ret=0 reason=anim_flag70` -> trace who owns/clears the animation loop flag;
- repeated `ret=0 reason=actor1264` -> trace owner/clear path for actor+0x1264;
- repeated `ret=0 reason=timing` -> compare current/end/duration progression and action707 descriptor timing;
- `ret=1 reason=pass` without 708 -> trace lookup(708)/vslot dispatch immediately downstream;
- native 707->708 appears -> do not mutate; follow the restored fallback 708->125->261->74.


## Compile-clean revision (2026-09-29)
The first R170 source drop failed under `-Werror` because retired R167/R168/R169 diagnostics left unused locals in `PlayActionProbeHook::Callback` and `P81OugiAwakeningPolicyHook::Callback`. The compile-clean revision removes only those unused declarations/reads (`pre_e80`, the local `pre_e94` in that PlayAction snapshot, `semantic_uj`, and unused P81 locals `action/e80/e98/ea4/bda4`). R170 hook targets, native arguments/returns, fingerprints, probe filter, P128 patch plan, and read-only policy are unchanged. The workflow label was also corrected from “Apply R169 overlay” to “Apply R170 overlay”.
