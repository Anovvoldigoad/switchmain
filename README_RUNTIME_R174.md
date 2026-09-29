# NSC2Switch Runtime R174 — D-Pad Selector/Fallback Trace

Parent: exact R173 full-source package built from the R172 Google Drive parent.

## Why R174 exists

R173 hardware A/B produced the same visible route in both logs:
`PlayAction 921 @ main+0x646CFC` -> `PlayAction 928 @ main+0x647080`
-> Event236 opcode23 `SPTYPE_ACTION10` -> PL_ANM index930 -> V2H safe suppression.

No opcode17/DPAD17_APPLY executed in either run because ACTION10 remains suppressed before its downstream event stream.

R173 also proved that the old actor+0x12B78..0x12B88 snapshot is not sufficient to identify direction:
the values differ strongly between the two runs while the executed action route remains identical.

## New static v1.70 proof

The native controller function at `main+0x646190` sets:
- X23 = actor + 0x104B4
- primary selector mode = [X23+0x1DB0] = actor+0x12264
- fallback selector mode = [X23+0x1DB4] = actor+0x12268
- selector/helper result = [X23+0x1D88] = actor+0x1223C

Native rodata table for mode 0..3 is exactly:
`[923, 924, 921, 922]`.

For the custom-character generic path, native code reaches `main+0x646CC8` with a candidate action in W20, calls:
`main+0x768E84(actor, candidate, 1)`.

At `main+0x646CE4`:
- if the lookup result is non-null, PlayAction receives the candidate;
- if the lookup result is null, native CSEL substitutes action921.

Therefore an observed PlayAction921 does NOT prove that the selector chose 921. It can be the native fallback after an action-descriptor lookup miss for 923/924/922.

## R174 markers

R174 reuses the existing PlayAction trampoline. Zero new hooks/trampolines.

Markers:
- `[NSC:R174] DPAD_SELECTOR_PRE ...`
- `[NSC:R174] DPAD_SELECTOR_POST ...`

New fields:
- `sel_primary` actor+0x12264
- `sel_fallback` actor+0x12268
- `sel_helper` actor+0x1223C
- `active_mode`
- `base_candidate`
- `fallback921_suspect`
- `q105f8/q105fc/q10600/q10610`
- old 12B78 block retained only as auxiliary evidence

Candidate mapping:
- mode0 -> 923
- mode1 -> 924
- mode2 -> 921
- mode3 -> 922

`fallback921_suspect=1` means the first route call reached PlayAction921 while the selector table says the base candidate was a different action.

## Safety

- no gameplay write
- no new hook/trampoline
- R172 UJ-miss direct-animation parity retained
- every non-UJ opcode23 stays V2H-safe-suppressed
- exact P128 30-word runtime delta retained
- V2N/V2P stage probes retained
- R164 stage asset untouched
- voice untouched
- no char281 gameplay branch
- no visibility/damage override

## Test

Use separate fresh boots:
1. Left D-pad once only, save full log.
2. Right D-pad once only, save full log.

Compare the first `DPAD_SELECTOR_PRE` line in each run.

Decisions:
- different `active_mode/base_candidate`, but one/both `index=921` with `fallback921_suspect=1`
  -> selector works; missing candidate action descriptor is the next compatibility gap.
- same `active_mode/base_candidate`
  -> direction selector is already collapsed upstream of `main+0x646CC8`.
- mode2/base_candidate921 in one run and a different candidate in the other
  -> native direction dispatch is healthy; only the non-921 candidate lookup path needs parity.
