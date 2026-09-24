# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R110

## Locked target
- Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
- Program ID `0100FA10190A0000`
- Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired patched main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Architecture invariants
- Generic/data-driven compatibility only; no gameplay `char_id == 281` branch.
- Required custom UJ sequence remains `700 -> 707 -> 708 -> 710 -> cinematic`.
- 708 is required and must not be suppressed.
- Do not force action710.
- Preserve P50 victim-safe Event236 shadow behavior.
- Preserve P89 generic actor-predicate bridge.
- No speculative writes to E94/E9C/EA4/BDA4/BDA8/BDC8.

## P102A runtime result — hypothesis falsified
P102A suppressed the exact native `708 -> 74` fallback call at `main+0x798F34`.
Observed result:
- after Kamui absorption, Tobi became movable again;
- however the UJ still remained stuck and did not enter cinematic;
- action710 was still not produced.

Conclusion:
- action74/control-lock was a downstream symptom;
- suppressing it improved movement but did not restore the missing 708->710 handoff;
- P102 HOLD74 is retired and must not remain active in the next build.

## Event236 / LOOP re-audit
The active custom Tobi LOOP variant is not the two LOOP records that contain frame16 Event236 opcode23 `SPSKILL_1_END`.
The active runtime variant is the third `PL_ANM_SPSKILL_1_LOOP` record whose frame16 event is Event121 `SW_MTOB_XH`.
Runtime already proved Event121 executes successfully and condition index512 `SW_MTOB_XH` is subsequently queried by native condition logic.
Therefore missing Event236 op23 is not the root of missing action710. P101 event-driven END theory is retired.

## SpecialCond runtime gap — source/static proof
Compiled custom runtime data contains:
- charID276 -> `COND_9ISH`
- charID281 -> `COND_2DNZ`

UltimateStormAPI `SpecialCondParam::Create_NSC` semantics are source-proven as:

```text
original(remap(characterSelector), context)
```

The second argument is preserved. The first input is looked up in the loaded specialCond map and, on a hit, replaced by the dispatcher index associated with the named `COND_*` entry.

Dispatcher-name table proof:
- `COND_2MDR` = index57
- `COND_2DNZ` = index58 (`0x3A`)
- Tobi compiled mapping therefore means `281 -> selector58`, not raw charID57.

Do not implement this as `281 -> 57` and do not rewrite actor E54.

## Switch selector table proof
The Switch v1.70 special-condition selector table is at `main+0x205E008`, 82 records, stride16, selector at `+0x08`.
Historical PC/Switch audit proved all 82 selector values and their order match.

Relevant Switch entries:
- selector58 exists and resolves to factory `main+0x7CC8E0`;
- selector276 exists;
- selector281 is absent from this 82-entry table;
- an unmapped selector falls back to selector0/default factory `main+0x7CBC80`.

Central dispatcher:
- `main+0x7CAB00`

Direct native callsite:
- `main+0x722F24`: load W0 selector
- `main+0x722F28`: load W1 context from `+0x2FC`
- `main+0x722F2C`: BL `main+0x7CAB00`

This matches the PC wrapper contract structurally: two integer-like inputs; selector first, context second.

## P103A functional candidate
P103A ports only the missing SpecialCond selector-remap semantic at `main+0x7CAB00`.

Generated current map:

```text
276 -> 276
281 -> 58
```

Runtime behavior:
1. receive native `(selector, context)` at `0x7CAB00`;
2. map selector through generated `specialCond` table;
3. call original exactly once as `Orig(mapped_selector, context)`;
4. return original factory result unchanged.

P103A does NOT:
- rewrite actor E54;
- force 708 or 710;
- suppress action74;
- write actor action/state/control fields;
- patch any of the raw Danzo charID57 callsites;
- modify condition index512 or its descriptor.

Native caller reloads its original selector/identity after the factory returns, so only the selected special-condition class is substituted.

## Hook / allocator budget
P103A adds exactly one new trampoline at `main+0x7CAB00` and no inline hooks.
P99 previously proved one additional trampoline on the P96 ancestry is boot-viable; P100B failed only after a large multi-hook allocation burst.

P103A fingerprints the first eight instructions at `0x7CAB00` before installation.

## Markers
Expected boot marker:

```text
[NSC:P103A] READY ... probe=1
```

When mapped selector281 is consumed:

```text
[NSC:P103A] REMAP ... selector=281 mapped=58 context=... ret=...
```

## Single-session test
1. Boot and confirm P103A READY `probe=1`.
2. Use custom Tobi and perform one Kamui UJ.
3. Observe whether native sequence proceeds `700 -> 707 -> 708 -> 710 -> cinematic`.
4. Confirm Tobi movement after the sequence.
5. Smoke-test Tobi as victim of enemy UJ to ensure P50 restore safety remains intact.
6. Send full Uzuy log + compiled P103A artifact.

## Interpretation
- `REMAP selector=281 mapped=58` + native 710/cinematic: missing SpecialCond factory mapping was the handoff blocker.
- `REMAP` occurs but still no 710: SpecialCond mapping is now correctly ported, but another post-factory consumer remains; do not revert mapping or force 710. Static-follow the factory58 object/consumer path next.
- no `REMAP` for Tobi: the battle path did not reach the expected SpecialCond factory boundary with selector281; inspect the factory creation lifecycle rather than action/state fallback.
- boot fails before READY: treat as trampoline allocator pressure; do not split into many hooks. Reuse/retire one older diagnostic trampoline while preserving P50/P89.
