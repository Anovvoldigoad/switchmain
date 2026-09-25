# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R115

## Locked target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Required custom UJ graph
`700 -> 707 -> 708 -> 710 -> cinematic`. Action708 is legitimate and must not be suppressed.

## P104B runtime proof
Successful vanilla char91 produced action710 from native PlayAction caller `main+0x7E6EC8`, which is inside sibling controller `main+0x7E64D4` (+0x520).
Failing custom Tobi produced `707 -> 708 -> 261 -> 74`; action261 was issued by native PlayAction caller `main+0x7DE558` / callsite `main+0x7DE554` in the +0x4C0 controller path.
P104B emitted no gate rows, so its `0x7EE8E0 / actor+0x12240` probe was not on the failing 708->261 invocation path.

## P105A boot failure — root cause proven
P105A added two new whole-function trampolines at `main+0x7DDD94` and `main+0x7E64D4`.
Boot log stopped after P96 READY and exlaunch aborted in `hook_impl.cpp` with:
`Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)`.
The diagnostic address flood `0x69696900000000` is exlaunch abort behavior, not a game actor pointer.
P105A never reached its READY marker. Therefore P105A is retired.

## P105B design — one new trampoline only
P105B parent is P96. P101/P102/P103/P104/P105A are not installed.
P105B spends the one empirically available extra trampoline only on:
- `main+0x7DDD94` (+0x4C0 controller), ABI `(actor, mode) -> void`.

It logs player-side focused action700..711 ENTER/EXIT with:
- original `mode` W1,
- exact caller/callsite,
- action pre/post,
- selected actor state fields,
- vtable +0x4C0/+0x520 targets.

The successful +0x520 controller remains completely native/unhooked. It is correlated through the already-installed P50/P59 PlayAction hook:
- `main+0x7E6EA8` prepares action710,
- `main+0x7E6EC4` calls PlayAction,
- runtime caller is `main+0x7E6EC8`.
Static scan proves `main+0x488B28` is the only direct BL into `main+0x7E64D4`.

P105B adds zero inline hooks, performs no actor/action/state/gate/mode/controller writes, no force708/710, and no char281 gameplay branch.

## Workflow robustness
Only `build-subsdk9-p105b.yml` is push-enabled. The drop-in also includes disabled legacy stubs for P103A/P104A/P104B/P105A so overlaying onto an existing repo disables stale push workflows instead of requiring manual deletion.

## Test
One boot/session:
1. Confirm `[NSC:P105B] READY ... probe=1` appears.
2. Successful vanilla char91 UJ.
3. Failing custom Tobi UJ.
4. Correlate P105B `CTRL4C0` rows with existing P59 PlayAction rows at callers `0x7DE558` (261) and `0x7E6EC8` (710).

The key next fact is the +0x4C0 `mode` and caller that encloses Tobi `708 -> 261`, compared against absence/presence of +0x4C0 during successful vanilla 707->710.
