# NSC2Switch Runtime V2F — Opcode23 No-PlayAction Causal A/B

Parent: V2E hardware run on the V2D original-main runtime architecture.

Original/restore main SHA256 (must remain deployed on disk):

`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

## What V2E proved

The latest hardware log is branch C from R147:

- Right D-Pad reaches custom action 928.
- Event236 opcode23 fires with `p2=0`, `p3=77`, `text=SPTYPE_ACTION10`.
- The custom PL_ANM resolver finds index `930`.
- The current Switch port calls `SetActionImmediate(target, 77)` and then incorrectly calls `PlayAction(target, 930)`.
- Runtime therefore becomes a hybrid: current action changes `928 -> 930` while the immediate-action field remains `77`.
- Later opcode17 executes correctly and writes Right charge `100.0f` (`42c80000`) to actor+`0x12B84`.
- Tobi still disappears, so opcode17 is no longer the frontier.
- Every observed Tobi `VIS_SHADOW` in this activation is `p2=1`; the log does not show opcode12 explicitly hiding Tobi.

## Exact PC source contract

UltimateStormAPI / MovesetPlus does **not** call PlayAction with the resolved animation index for opcode23. It does:

1. `ccPlayer::SetActionImmediate(target, action)`
2. resolve the string through `PlAnmList`
3. `ccPlayer::SetAnmDirect(target, pl_anm_id)`

For this fixture that means action `77` plus PL_ANM index `930`, not action `930`.

A Switch `SetAnmDirect` address has not yet been proven. V2F deliberately does not guess one.

## V2F A/B change

Only opcode23 changes relative to V2E:

- keep `SetActionImmediate(target, param3)` exactly as before;
- keep PL_ANM string resolution exactly as before;
- when opcode23 resolves the PL_ANM index, **do not call `PlayAction(index)`**;
- emit a dedicated marker and return;
- opcode22 remains unchanged as the control path;
- opcode17 source-parity write remains unchanged;
- no visibility force is added;
- no char-specific branch is added;
- UJ/P128/V2D runtime patch architecture is unchanged.

Expected marker:

```text
[NSC:V2F] OP23_NO_PLAYACTION_AB ... action_param=77 text=SPTYPE_ACTION10 pl_anm_index=930 ... playaction_suppressed=1 setanmdirect_unresolved=1 diagnostic_only=1
```

## What this build is for

This is a **one-variable causal A/B**, not the final opcode23 port. Because `SetAnmDirect` is intentionally absent, the direct PL animation and downstream events normally produced by that animation may also be absent. Do not judge final Izanagi parity from this build. Judge only disappearance and the action-state route.

### Outcome A — Tobi no longer disappears

This proves the V2E `PlayAction(930)` substitution is causally responsible for the disappearance. The next build must resolve/validate the real Switch `SetAnmDirect` and replace the diagnostic suppression with exact source parity.

### Outcome B — Tobi still disappears

Then the disappearance originates before the wrong `PlayAction(930)` transition—most likely action928 / immediate action77 / another paired event—and the next trace must focus there. Do not return to opcode17 and do not globally force visibility.

## Minimal hardware test

1. Fresh boot; confirm V2D resolver 7/7 and 30-word runtime patch READY.
2. Confirm Naruto own UJ, Tobi victim UJ, and Tobi own UJ still pass if practical.
3. Press Right D-Pad once.
4. Confirm the V2F marker appears with action_param=77 and pl_anm_index=930.
5. Record only whether Tobi disappears or remains visible, and whether control remains usable.
6. Save the full log immediately.

Do not use Left D-Pad or stack additional state changes before saving the log.
