# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R112

## Locked target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Required custom UJ graph
`700 -> 707 -> 708 -> 710 -> cinematic`. Action708 is legitimate and must not be suppressed.

## P103A result
P103A source-faithful specialCond factory remap executed at runtime (`281 -> 58`), but no action710 appeared. Custom still ran `707 -> 708 -> 261 -> 74`. Therefore specialCond selector mapping is real but not the missing-710 root by itself.

## New static sibling-controller proof
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

## P104A design
One new whole-function trampoline only, at `main+0x7EE8E0`.
At exact caller return `main+0x7DE028` and focused actions700..711 it logs:
- native predicate return (gate1),
- `actor+0x12240` (gate2),
- action/state pre/post,
- vtable slot +0x4C0 and +0x520 targets.

P104A parent is P96. P101/P102/P103 are not installed. P50 victim-safe shadows and P89 generic admission bridge remain preserved. P104A is read-only: no actor/action/state/control/gate writes, no return override, no force708/710, no char281 gameplay branch.

## Test
One session: successful vanilla char91 UJ, then failing custom Tobi UJ. The first different gate determines the next functional target.
