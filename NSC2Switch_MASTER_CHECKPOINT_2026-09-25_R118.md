# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R118

## Locked target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Locked history — do not reopen
- P50 victim-safe Event236 shadow stays.
- P89 solved generic UJ admission; custom reaches `700 -> 707 -> 708`.
- 708 is legitimate. P97 suppress-708 failed.
- P98B proved exact state125 request during action708 from caller `0x7EB28C`.
- P101 HOLD125 did not produce 710. P102 HOLD74 only restored movement.
- P99 proved state125/261/74 are downstream cleanup after the missing handoff.
- P103 SpecialCond `281 -> 58` executes but is insufficient.
- P104 gate hypothesis retired.
- P105B proved state125 generic dispatch selects +0x4C0 mode0 and produces 261.

## P106A decisive result
Compiled artifact and log50 are valid. P106A READY reached with one trampoline at
`main+0x7E64D4` (+0x520).

Full log result:
- 254 CTRL520 rows total = 127 player-side invocations.
- char91: 254 rows.
- char281: ZERO rows.
- vanilla first mode0 invocation enters +0x520 from generic dispatcher return
  `0x7A8354` / callsite `0x7A8350` with action707 and exits action710.
- native PlayAction710 occurs inside at caller `0x7E6EC8` / callsite `0x7E6EC4`.
- custom still runs 707->708, E9C becomes125, state commits E94=125/E98=63,
  then native PlayAction261 at `0x7DE558` and fallback74.

Therefore custom does not enter +0x520 and fail internally. The divergence is the
state/controller selection before the shared generic dispatcher BLR `0x7A8350`.

## Static state/controller selection proof
- `0x7A8310`: read active E94.
- state record is indexed at stride 0x20.
- `0x7A834C`: mode=0.
- `0x7A8350`: BLR selected state controller.
- successful vanilla committed state137 and dispatches +0x520.
- custom cleanup commits state125 and dispatches +0x4C0.

Exact custom cleanup producer:
- `0x7EB27C`: MOV W1,#125
- `0x7EB288`: BLR state-request vslot
- return/caller `0x7EB28C`
- P98B runtime proved this reaches base state request `0x7A89A4` and queues E9C=125.

## P107A functional candidate
Replace P106 diagnostic trampoline with exactly one trampoline at state request
`main+0x7A89A4`.

On the exact proven post-708 cleanup fingerprint only, map the native request
`125 -> 137` and call original state-request once with unchanged arg2/arg3.
Native validation, native E9C store, state commit, controller lookup and
PlayAction remain untouched.

Guard:
- player side0;
- semantic UJ active;
- generated ougiAwakening membership;
- exact caller return `0x7EB28C`;
- requested state125;
- arg2=1, arg3=0;
- current action708;
- E94=63, E98=136, E9C=0;
- BDA4=1, BDA8=0, BDC8=0.

P107A contains no char281 gameplay branch, no direct state/action/control write,
no force708 and no force710.

This is a functional candidate, not a claim that a native post-708 donor was
observed using state137. The justification is the combined P98/P101/P102/P105/P106
proof: holding cleanup is insufficient, but state125 prevents entry to the proven
native 710 controller while state137 dispatches that controller in the successful
native control.
