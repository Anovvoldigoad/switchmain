# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R108

## Locked target
- Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
- Program ID `0100FA10190A0000`
- Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch `229bbd6`

## Architecture invariants
- Generic/data-driven compatibility only; no gameplay `char_id == 281` branch.
- Required custom UJ sequence remains `700 -> 707 -> 708 -> 710 -> cinematic`.
- Do not suppress required 708.
- Do not force 710.
- Preserve P50 victim-safe Event236 shadow behavior.
- Preserve P89 generic actor-predicate bridge.
- No speculative writes to E94/E9C/EA4/BDA4/BDA8/BDC8.

## P101A artifact/log45 audit
Uploaded P101A artifact is valid:
- internal SHA256SUMS PASS;
- paired/restore main hashes match locked baselines;
- compiled subsdk9 SHA256 `7e72791d9ad68e27e62928d24d9e4d821c63652f0f62e36cb8138a4ff6bb47b4`.

Runtime:
- P101A READY appears and probe=1.
- custom attacker enters action708 natively.
- P101A HOLD125 fires once at action708, E94=63, E98=136, E9C=0, EA4=0x5DC, BDA4=1.
- Event236 op23 never appears.
- Therefore waiting for op23 is falsified.
- Later, while current action is still 708, native PlayAction74 is issued from runtime caller `main+0x798F34`.
- Immediately before that fallback, actor state includes E94=1, E98=63, E9C=0, BDA4=1, BDC8=0.
- Native call succeeds and changes 708 -> 74 while BDA4 remains 1, matching the observed symptom: Tobi is visible/alive after absorption but cannot move.

## Exact static proof of fallback74 producer
Pinned paired main disassembly:
- `main+0x798E68`: `LDR W8,[X19,#0xE98]`
- `main+0x798E6C`: `MOV W1,#74`
- `main+0x798E70`: `CMP W8,#124`
- `main+0x798E74`: `B.NE main+0x798F1C`
- `main+0x798F1C`: `FMOV S0,#1.0`
- `main+0x798F20`: `MOV W2,#-1`
- `main+0x798F24`: `MOV X0,X19`
- `main+0x798F28`: `MOV W3,WZR`
- `main+0x798F2C`: `MOV W4,WZR`
- `main+0x798F30`: `BL PlayAction`
- runtime return/caller marker: `main+0x798F34`.

Thus `0x798F34` is a proven exact action74 fallback callsite, not a generic caller.

## P102A functional candidate
P102A removes the P101 state125 guard and restores Event236 op23 to ordinary P50 handling.
It adds ZERO new trampolines and reuses the existing P50 PlayAction trampoline.

P102A suppresses only the exact native PlayAction74 call when ALL are true:
- caller return `0x798F34`;
- requested index `74`;
- current action `708`;
- semantic UJ latch active;
- generated OugiAwakening membership true;
- E98=63;
- E9C=0;
- BDA4=1;
- BDC8=0.

On a match it returns `1`, matching the observed native PlayAction74 success return, without calling Orig and without mutating actor fields. The caller then continues natively.

Safety bound:
- maximum 16 matching suppressions per UJ;
- then `[NSC:P102A] FAILOPEN74` and native behavior resumes;
- counter resets on new PlayAction700 and semantic UJ latch lifecycle.

Markers:
- `[NSC:P102A] READY`
- `[NSC:P102A] HOLD74`
- `[NSC:P102A] FAILOPEN74`

## P102A decision tree
1. `HOLD74` then native `PlayAction710` from `0x7E6EC8` -> fallback74 was pre-empting the 710 handoff; validate cinematic and control restoration.
2. `HOLD74` but no 710, then `FAILOPEN74` -> fallback74 is downstream symptom, not root; use resulting state to identify the next native gate, but do not force 710.
3. No `HOLD74` -> runtime fingerprint differs; inspect exact pre-call state before changing policy.
4. 710/cinematic works but control still locked -> isolate post-cinematic control-release path; do not write BDA4 directly without proof.

## Test request
Single Tobi UJ is sufficient for the candidate test. After Kamui absorbs the opponent, observe:
- whether 710/cinematic begins;
- whether Tobi regains movement afterward;
- whether opponent restore remains correct.
Upload full log + compiled P102A artifact.
