# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R116

## Locked target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Required custom UJ graph
`700 -> 707 -> 708 -> 710 -> cinematic`. Action708 is legitimate and must not be suppressed.

## Proven runtime divergence before P105B
- Vanilla char91: action710 is issued by PlayAction caller `main+0x7E6EC8` inside native sibling controller `main+0x7E64D4` (+0x520).
- Custom Tobi: `707 -> 708 -> 261 -> 74`; action261 is issued by PlayAction callsite `main+0x7DE554` / caller `main+0x7DE558` in the +0x4C0 controller path.
- P104B's old `0x7EE8E0 / actor+0x12240` gate probe produced no focused rows and is retired as the decisive target.

## P105A retired
P105A added two new whole-function trampolines and failed before READY because exlaunch's trampoline allocator exhausted its available pool (`Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)`).

## P105B design
P105B parent is P96 and uses exactly one new whole-function trampoline at `main+0x7DDD94` (+0x4C0), ABI `(actor, mode) -> void`.
The +0x520 sibling at `main+0x7E64D4` remains fully native/unhooked and is correlated through existing P59 PlayAction caller `main+0x7E6EC8`.
P105B is read-only: no action/state/gate/mode/controller writes, no force708/710, and no char281 gameplay branch.

## R116 compile-safe logging fix
The first P105B revision failed compilation before link because its READY format string could expand to 539 bytes while `LoggerMgr::Log` uses a 512-byte `snprintf` buffer and warnings are errors.
R116 changes logging only:
- READY is shortened to a conservative maximum of 209 bytes.
- `CTRL4C0` holds controller/caller/action/vtable metadata, conservative maximum 307 bytes.
- `STATE4C0` holds actor-state pre/post fields, conservative maximum 320 bytes.
- `CTRL4C0` and `STATE4C0` share `seq` and `phase` for deterministic pairing.
- `verify_p105b_source.py` now enforces every P105B log record's conservative bound `<512`.
No hook, target offset, parent, gameplay policy, or main binary changed.

## Static locked proof
- `main+0x7DE554 -> PlayAction 0x766B8C` (custom 261 producer path).
- `main+0x7E6EC4 -> PlayAction 0x766B8C` (vanilla 710 producer path).
- `main+0x488B28 -> 0x7E64D4` and it is the only direct BL to +0x520 found by the verifier.

## Test
One boot/session:
1. Confirm `[NSC:P105B] READY ... probe=1`.
2. Successful vanilla char91 UJ.
3. Failing custom Tobi UJ.
4. Correlate P105B `CTRL4C0` + `STATE4C0` pairs with P59 PlayAction callers `0x7DE558` (261) and `0x7E6EC8` (710).

The next decisive fact is the +0x4C0 `mode` and caller enclosing Tobi `708 -> 261`, compared with the successful vanilla +0x520 path.
