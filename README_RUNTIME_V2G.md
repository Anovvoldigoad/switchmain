# NSC2Switch Runtime V2G — Opcode23 Direct-Animation Parity Candidate

Parent: V2F hardware causal A/B on the V2D original-main runtime architecture.

Original/restore main SHA256 (must remain deployed on disk):

`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

## What V2F proved on hardware

- Right D-Pad no longer makes Tobi disappear when opcode23's wrong `PlayAction(930)` call is suppressed.
- The same run still leaves Tobi vulnerable to normal damage.
- Opcode23 is `p3=77`, `text=SPTYPE_ACTION10`; the PL_ANM resolver returns index `930`.
- V2F performs `SetActionImmediate(77)` but intentionally does not play PL_ANM 930, so the Izanagi activation animation/event chain is incomplete.
- UJ/P128 behavior, original-main resolver architecture, and the exact 30-word runtime patch remain the baseline and are not reopened here.

Therefore the V2E wrapper substitution contained both a needed direct-animation operation and unwanted extra PlayAction behavior.

## New static correction: main+0x766320 is the direct-animation core

Earlier P57 logs called the field at decimal offset `4712` an "action". Decimal 4712 is actually hexadecimal `0x1268`. Static v1.70 analysis shows this is animation state:

- `main+0x766320` saves `w1` as the requested index and preserves incoming `v0/s0` as the rate.
- Near its successful tail it writes:
  - actor+`0x1264` = animation-valid flag,
  - actor+`0x1268` = requested/resolved animation index,
  - actor+`0x126C` = incoming float rate,
  - actor+`0x1270` / `0x1274` = related timing/state.
- Multiple unrelated native callers invoke `main+0x766320` directly with the same ABI:
  - `x0 = actor`
  - `w1 = animation index` (examples 934, 936, 938, 940, 942/943)
  - `w2 = -1`
  - `w3 = 0`
  - `s0 = 1.0f`
- `main+0x766B8C` is the stronger wrapper used by the old compatibility code. It first dispatches actor vtable+`0xF98`, whose locked-build target is `main+0x766320`, and then executes additional stage-2 logic at `main+0x766CAC`.

This explains the A/B cleanly:

- V2E: direct animation **plus** extra wrapper/stage2 -> animation can progress, but Tobi disappears.
- V2F: neither direct animation nor stage2 -> Tobi stays visible, but Izanagi does not complete.
- V2G: direct animation only -> the expected source-parity candidate.

## Exact opcode23 behavior in V2G

For opcode23 only:

1. keep `SetActionImmediate(target, param3)` at the proven Switch immediate-action function (`main+0x7A8438`);
2. resolve the event string through the existing PL_ANM lookup;
3. obtain the already fail-closed `CENTRAL_SETTER` resolver anchor (locked v1.70 resolves uniquely to `main+0x766320`);
4. call it with native direct-animation ABI `(target, pl_anm_index, -1, 0, 1.0f)`;
5. do **not** call `main+0x766B8C` and do **not** enter `main+0x766CAC` from opcode23.

Opcode22 remains unchanged for this first hardware A/B. If V2G passes, opcode22 can be migrated separately in the next parity-cleanup build.

Expected marker for the fixture:

```text
[NSC:V2G] OP23_DIRECT_ANM ... action_param=77 text=SPTYPE_ACTION10 pl_anm_index=930 direct_off=0x766320 ... anm1268=928->930 e94=...->77 ... playaction_wrapper=0 stage2_766cac=0 source_parity_candidate=1
```

The exact `anm1268_before` value can vary with the activation frame; the important postconditions are PL_ANM index 930 at `+0x1268`, action request 77 at `+0xE94`, and no opcode23 wrapper/stage2 call.

## P57 trampoline ABI correction

The historical P57 trace hook at the same resolved entry previously declared only the integer arguments. Static prologue word `MOV V8.16B,V0.16B` and native callers prove that `s0` is a live float rate argument. V2G changes the tracing callback to `(actor,index,a2,a3,float rate)` and forwards the rate to `Orig(...)`, so the diagnostic trampoline cannot discard/corrupt direct-animation rate semantics.

No character-specific behavior is added.

## Minimal hardware test

1. Fresh boot; confirm resolver `7/7`, fail-closed=1, and exact 30-word runtime patch READY.
2. Press **Right D-Pad once** on custom Tobi.
3. Confirm `[NSC:V2G] OP23_DIRECT_ANM` reports `action_param=77`, `pl_anm_index=930`, `direct_off=0x766320`, and `anm1268_after=930` (shown as the right side of `anm1268=A->930`).
4. Confirm Tobi stays visible.
5. Watch for downstream `SW_MTOB_XH` and opcode17 Right write `42c80000` (100.0f).
6. Let the enemy land repeated normal hits. Check whether HP damage is prevented and substitution recovery occurs.
7. Save the complete log immediately.
8. After that, optionally test Left D-Pad reset and the already-solved UJ regressions.

### Decision

- If Tobi remains visible **and** Izanagi prevents normal damage: opcode23 direct-animation semantics are functionally confirmed; migrate opcode22 in the next cleanup.
- If Tobi remains visible but still takes damage: inspect whether `SW_MTOB_XH` and opcode17 Right=100 occur after the V2G marker. Do not return to visibility forcing or UJ admission.
- If disappearance returns despite `playaction_wrapper=0`: the direct PL_ANM itself triggers another downstream event and the new log will identify that route.
