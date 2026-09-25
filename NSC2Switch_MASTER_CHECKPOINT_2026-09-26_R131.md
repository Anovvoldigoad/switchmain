# NSC2Switch MASTER CHECKPOINT — 2026-09-26 R131

## Target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pinned commit: `229bbd6`

## Locked runtime result from P116A
Artifact audited:
- outer runtime ZIP SHA256: `05333ffd8075f016607ae1d628a88ed4d33e553375aeb2c011ae15836f8ac9a3`
- compiled subsdk9 SHA256: `689a4e615067223badcc0a454fc91ebd04d4fdb1d6a9dd6dabfd4d541fbd87fe`
- subsdk9 Build ID: `B1BA5CC8B13C65BE6CEF5DE1EA1BA93FAFE6A311`
- ZIP CRC PASS; SHA256SUMS PASS; paired/restore main exact.

P116 runtime:
- `[NSC:P116A] READY ... probe_ok=1`
- total `[NSC:P116A] CALL` rows: **1**
- successful vanilla char91 action707:
  - caller return `0x77C5EC`, bucket5
  - native ret=1
  - session9 `0 -> 1`
  - session10 `0 -> 1`
  - peer char97 action74
- vanilla then reaches native action710.
- custom Tobi char281 executes `74 -> 700 -> 707 -> 708`, but has **zero** P116 calls.
- Therefore custom Tobi never reaches `main+0x7EF098` through any of its six direct native callers.

## Important correction
The universal cinematic outer setup has six direct BL callers:
- `0x0D6BDC -> 0x7EF098`
- `0x0FBF60 -> 0x7EF098`
- `0x32F570 -> 0x7EF098`
- `0x753CB8 -> 0x7EF098`
- `0x77C5E8 -> 0x7EF098`
- `0x802634 -> 0x7EF098`

Current vanilla fixture used bucket5 (`0x77C5E8`, return `0x77C5EC`). Tobi used none of the six.

## Static bucket5 back-slice
Large action-event dispatcher entry is `main+0x77B560`.
Relevant sequence:
- `0x77B590 BL 0x3F4B00` resolves current event pointer.
- `0x77B5A4 MOV X20,X0` leaves event pointer in X0/X20.
- `0x77B5A8 BL 0x3F4BC0`; return `0x77B5AC`.
- `0x77C474 LDR W8,[X20,#0x50]` reads raw event type.
- `0x77C478 AND W9,W8,#0xFFFFFFFE`.
- `0x77C47C CMP W9,#10` => raw event type 10 or 11 is the cinematic preflight family.
- after native readiness/pairing corridor, `0x77C5E8 BL 0x7EF098` creates the outer cinematic setup.

`main+0x3F4BC0` is a tiny global getter. It ignores X0, which means a wrapper can preserve the stale native X0 event pointer from `0x77B5A8` while still calling Orig once.

## P117A design
Name: **P117A Action-Event Stream Census**
Parent: P96/P89/P50 baseline.
Read-only diagnostic.

Exactly one new trampoline:
- `main+0x3F4BC0`

Focus filter:
- capture LR first.
- only log `caller_off == 0x77B5AC`.
- every other caller immediately returns `Orig(event_x0)`.

Focused event snapshot:
- event pointer carried in X0
- event+0x28 payload bits
- event+0x48 mask
- event+0x50 raw type
- normalized type = raw & ~1
- `type10_11 = 1` iff normalized type == 10
- native getter return value

No branch patch, no event write, no session creation, no state mapping, no direct state write, no force708/710, no char281 gameplay branch.

## P117 decision tree
1. Vanilla UJ window contains `type10_11=1`; Tobi 707/708 window contains none:
   - root frontier moves upstream to custom/generated action-event descriptor/producer.
   - do not force session/state.
2. Both vanilla and Tobi contain `type10_11=1`:
   - event stream exists; next probe actor/peer `+0xC48` readiness gates one at a time.
3. No clean vanilla type10/11 row:
   - inspect fixture/event sequence; do not infer from absence.

## Retired as root
- state125/126 victim path as universal UJ requirement.
- state125->136 and state125->137 mappings.
- force710.
- suppress action708.
- B968 manager blocker.
- direct manager/session creation.
- P114/P115 bucket5 type9/event gate conclusions as universal across all vanilla characters.
- P116 whole-function outer census after its result established custom CALL=0.
