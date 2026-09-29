# NSC2Switch MASTER CHECKPOINT — 2026-09-29 R174

## Frozen identity
- Game: NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- original/active main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- original-main runtime architecture retained
- resolver 7/7 retained
- exact runtime patch delta retained: 30 words = condition5 + P67 1 + P128 24
- P128 retained
- R164 StageInfo CPK hardware PASS asset retained
- voice skipped/frozen
- no char281 final gameplay branch

## Solved/frozen
### UJ
R172 direct-animation parity remains the active UJ fix:
PC opcode23 semantics = SetActionImmediate(param3) -> resolve PL_ANM -> SetAnmDirect(index).
Switch `main+0x766320` is the proven direct-animation primitive.
Scope stays self/side0 + custom semantic UJ + OugiAwakening member + animation707 + requested state8.
No force708/710/74/77.
Non-UJ opcode23 remains V2H safe-suppressed.

The startup R172 fingerprint can print fail after the same setter has already been hooked read-only; the actual opcode23 UJ branch itself is not gated by that READY boolean. Do not treat the startup line alone as UJ deployment failure.

### Stage
R164 StageInfo-fixed asset remains frozen and must not be deleted:
`Tobi_Switch_R164_STAGEINFO_FIXED.zip`.

## R173 hardware input
Compiled artifact:
- `NSC-RUNTIME-R173-dpad-route-trace.zip`
- ZIP SHA256 `f649a5b31081206f9940509da0155fcb51c524fb56afa288726a0c449b0d7e2c`
- subsdk9 SHA256 `5357eee75d9b5a771f1a29f3171057a7a43872a94d97d35f31a78fe5fda3e70d`
- main is exact original hash above

Logs:
- `uzuy_log(12).txt` SHA256 `0e332afe12e2b27b72c77304601a9c5794a42286d2874f34b6471b94c029ed09`
- `uzuy_log(13).txt` SHA256 `996405311b7b3843d7807f29429c1a1ec97d64b011d9f69f63566c22b1d6679a`

If the requested test order was followed, log12 is Left and log13 is Right. The core R173 conclusion is label-independent because both execute the same route through ACTION10.

## R173 hardware verdict
Both runs:
1. `DPAD_ROUTE_PRE` at caller LR `0x646CFC`, PlayAction index921, animation74.
2. PlayAction changes animation74->921.
3. `DPAD_ROUTE_PRE` at caller LR `0x647080`, PlayAction index928.
4. PlayAction changes animation921->928.
5. Event236 opcode23 p3=77 text=`SPTYPE_ACTION10`.
6. PL_ANM lookup finds index930.
7. V2H safe suppression keeps animation928 and changes E94 152->77.
8. zero opcode17 / zero DPAD17_APPLY.

R173 12B78 block differs substantially between the two runs while the executed chain is identical. Therefore that block alone is not the direction selector frontier.

## R174 new static root boundary
Disassembly of original v1.70 `main+0x646190` proves:
- `X23 = actor + 0x104B4`
- selector primary `[X23+0x1DB0]` = actor+`0x12264`
- selector fallback `[X23+0x1DB4]` = actor+`0x12268`
- selector/helper result `[X23+0x1D88]` = actor+`0x1223C`

Native mode table at rodata VA `0x1B29960`:
- mode0 -> action923
- mode1 -> action924
- mode2 -> action921
- mode3 -> action922

For custom Tobi char281, the generic branch reaches `main+0x646CC8` with this candidate action.

Exact native sequence:
- call `main+0x768E84(actor, candidate, 1)`
- test returned pointer
- if non-null: PlayAction(candidate)
- if null: CSEL substitutes PlayAction(921)

Therefore previous inference "both inputs selected 921" is RETIRED.
Observed action921 can be a native fallback after candidate descriptor lookup failure.

`main+0x768E84` is statically confirmed as an action-record lookup path: it normalizes the requested action when requested and resolves it through actor+0x218 / native lookup `main+0x438E60`.

## R174 functional scope
Read-only, zero-extra-trampoline extension of the existing PlayAction hook.

At the proven route callsites, log:
- actor+0x12264 primary selector
- actor+0x12268 fallback selector
- actor+0x1223C selector/helper result
- active selector mode
- native base candidate derived from [923,924,921,922]
- actual PlayAction index
- `fallback921_suspect`
- q105f8/q105fc/q10600/q10610
- old 12B78 block as auxiliary evidence only

Markers:
`[NSC:R174] DPAD_SELECTOR_PRE ...`
`[NSC:R174] DPAD_SELECTOR_POST ...`

No action/state/input/visibility/damage writes.

## R174 decision table
- Left/Right different active_mode/base_candidate + one or both actual index921 with `fallback921_suspect=1`
  => direction selector is healthy; missing action-descriptor compatibility for candidate922/923/924 is next.
- Left/Right same active_mode/base_candidate
  => direction selection is already collapsed upstream.
- one mode is 2/candidate921 and the other is another candidate
  => strongest proof of healthy direction selector plus a specific non-921 lookup miss.

## Retired D-pad hypotheses
- opcode17 <=16 clamp: retired; source parity already solved.
- F30 activation-success flag: retired.
- DMGHIT_OFF/BODHIT_OFF as one-minute immunity: retired; they are short activation lifecycle events.
- global visibility/no-damage workaround: forbidden.
- global SetAnmDirect suppression/force: forbidden.
- "921 proves selector chose the same direction": retired by R174 static fallback proof.
- actor+0x12B78 block alone identifies Left/Right: retired as insufficient.

## Next hardware test
1. Build `NSC-RUNTIME-R174-dpad-selector-fallback-trace`.
2. Fresh boot -> Left once only -> save full log.
3. Fresh boot -> Right once only -> save full log.
4. Compare first R174 selector marker from each run.
5. Do not test UJ in the same boot unless regression verification is specifically needed.

END R174
