# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R114

## Locked target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Required custom UJ graph
`700 -> 707 -> 708 -> 710 -> cinematic`. Action708 is legitimate and must not be suppressed.

## P104B runtime result — gate hypothesis retired
The P104B artifact loaded successfully (`[NSC:P104B] READY`), but the complete one-session log contained zero P104B `GATE` rows. In that same session the action provenance remained fully visible through inherited traces, so the absence is meaningful: the exact `0x7EE8E0` caller probe did not observe the failing `708 -> 261` invocation. P104B gate1/gate2 must therefore not be used as the next functional target.

## Direct runtime ground truth
Successful vanilla char91:
- current action707;
- requested action710;
- PlayAction caller return `main+0x7E6EC8` (callsite `main+0x7E6EC4`);
- action changes `707 -> 710` and cinematic path proceeds.

Failing custom char281:
- `707 -> 708` is legitimate, with action708 requested from caller return `main+0x7725D0`;
- later, while current action708, requested action261 is issued from caller return `main+0x7DE558` (callsite `main+0x7DE554`);
- action changes `708 -> 261`, then `261 -> 74`.

## Sibling-controller static proof
Relevant actor-vtable family:
- slot `+0x4C0 -> main+0x7DDD94`, ABI `(actor, mode)`, no defined return value;
- slot `+0x520 -> main+0x7E64D4`, ABI `(actor, mode)`, no defined return value.

`main+0x7DDD94` begins by dispatching W1 mode 0/1/2. Its control flow contains candidate selection `MOV W20,#262` at `0x7DE3A0`, `MOV W20,#261` at `0x7DE3BC`, and the observed selected-action PlayAction callsite `0x7DE554 -> 0x766B8C`. The apparent RET at `0x7DE4D8` is not a terminal function boundary: `0x7DE4BC` can branch over that epilogue to `0x7DE4DC`, and the continuation later reaches the `0x7DE554` callsite.

`main+0x7E64D4` also dispatches W1 mode 0/1/2. It contains `MOV W1,#710` at `0x7E6EA8` followed by PlayAction `0x7E6EC4 -> 0x766B8C`; runtime vanilla returned at `0x7E6EC8`, directly matching this producer. Its sole direct BL entry call is `0x488B28 -> 0x7E64D4` (return `0x488B2C`).

## P105A question
Determine, without gameplay mutation:
1. which sibling controller is invoked around successful vanilla `707 -> 710`;
2. which sibling controller is invoked around custom `708 -> 261`;
3. the exact incoming W1 `mode` for each invocation;
4. the caller LR/callsite that selected each controller;
5. whether both controllers are invoked and ordering differs, or custom never reaches the +0x520 controller in the critical corridor.

## P105A design
Parent is clean P96. P101/P102/P103/P104 are not installed. P50 victim-safe shadows and P89 generic admission bridge remain preserved.

Exactly two new whole-function read-only trampolines:
- `main+0x7DDD94` (+0x4C0 controller);
- `main+0x7E64D4` (+0x520 controller).

Each captures X30 before any helper, then for player side only records:
- controller identity and entry offset;
- W1 mode;
- caller return and derived callsite;
- action/state at ENTER and EXIT;
- `e60/e70/e90/e94/e98/e9c/ea0/ea4`;
- `bda4/bda8/bdc8`;
- vtable +0x4C0/+0x520 target offsets.

Native `Orig(actor, mode)` is executed with the original arguments and no controller/action/state/gate/mode/return override is performed. There is no char281 gameplay branch and no force708/710.

## Test
One session:
1. successful vanilla char91 UJ through cinematic;
2. failing custom Tobi UJ through `700 -> 707 -> 708 -> 261 -> 74`.

The decisive result is the first reproducible controller/mode/caller difference surrounding vanilla `707 -> 710` versus custom `708 -> 261`. Do not force action710 until controller-selection provenance is known.
