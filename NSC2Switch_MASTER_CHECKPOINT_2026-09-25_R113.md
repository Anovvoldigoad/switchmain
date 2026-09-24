# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R113

## Locked target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Required custom UJ graph
`700 -> 707 -> 708 -> 710 -> cinematic`. Action708 is legitimate and must not be suppressed.

## Prior proof retained
P103A source-faithful specialCond factory remap executed at runtime (`281 -> 58`), but no action710 appeared. Custom still ran `707 -> 708 -> 261 -> 74`. Therefore specialCond selector mapping is real but not the missing-710 root by itself.

The relevant actor vtable family contains:
- slot `+0x4C0 -> main+0x7DDD94`
- slot `+0x520 -> main+0x7E64D4`

`main+0x7DDD94` is a `(actor, mode)` controller and contains the path that selected action261 after custom action708. The desired action710 producer is inside sibling controller `main+0x7E64D4`.

Before the 262/261 selector, +0x4C0 executes:
```asm
0x7DE020 MOV X0,X19
0x7DE024 BL  0x7EE8E0
0x7DE028 CBZ W0,0x7DE4C0
0x7DE02C LDR W8,[X23,#0x1D84]
0x7DE030 CBZ W8,0x7DE4C0
```
At function entry, `X23 = actor + 0x104BC`; therefore the second read is exactly `actor+0x12240`.
Only if native predicate `0x7EE8E0` and `actor+0x12240` are both nonzero can +0x4C0 continue toward its 262/261 action selector.

## P104A audit correction
P104A was structurally read-only but sampled `actor+0x12240` before calling `Orig(actor)` at `0x7EE8E0`. Native +0x4C0 reads that field only after the predicate returns, at `0x7DE02C`. Therefore P104A gate2 logs were timing-ambiguous and must not be used as decisive proof by themselves.

## P104B design
One new whole-function trampoline only, still at `main+0x7EE8E0`.

The hook captures caller LR before any helper call. For non-target callers it executes native `Orig(actor)` and returns without actor-state instrumentation. For exact caller return `main+0x7DE028`, player side only (`side==0`), and focused actions700..711 it logs:
- native predicate return (`pred`, gate1),
- `actor+0x12240` immediately before native predicate (`gate12240_pre`),
- `actor+0x12240` immediately after native predicate (`gate12240_post`),
- whether gate2 changed during predicate,
- action/state pre/post,
- vtable slot +0x4C0 and +0x520 targets.

`gate12240_post` is the authoritative P104B gate2 sample. Native predicate executes exactly once and its return is preserved unchanged.

P104B parent is P96. P101/P102/P103 are not installed. P50 victim-safe shadows and P89 generic admission bridge remain preserved. P104B adds no actor/action/state/control/gate writes, no return override, no force708/710, and no char281 gameplay branch.

## Analyzer hard validation
A P104B row is accepted only when:
- `side == 0`
- `caller_off == 0x7DE028`
- `slot4c0_off == 0x7DDD94`
- `slot520_off == 0x7E64D4`

## Test
One session only:
1. successful vanilla char91 UJ to cinematic;
2. failing custom Tobi UJ through `700 -> 707 -> 708`.

Interpret the first reproducible difference using `pred` and `gate12240_post`:
- `pred=0`: first gate closed;
- `pred!=0`, `gate12240_post=0`: second gate sampled closed;
- both nonzero: both sampled gates open, continue investigation downstream toward the 262/261 selection/handoff.

If `gate12240_changed=1`, use POST rather than PRE for diagnosis.
