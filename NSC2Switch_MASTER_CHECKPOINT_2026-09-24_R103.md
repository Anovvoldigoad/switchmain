# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R103

## Baseline
- Title: Naruto x Boruto Ultimate Ninja Storm Connections — Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin: `229bbd6`

## Locked architecture
- Generic/data-driven compatibility only; char281 is a diagnostic fixture, never a gameplay branch.
- Preserve P50 victim-safe Event236 shadow.
- Preserve P89 generic actor-predicate admission bridge.
- Do not force actions 700/708/710.
- Do not write E94/E9C/EA4/BDA4/BDA8/BDC8 speculatively.
- Do not globally patch wrapper main+0x772594.
- Prefer zero-extra instrumentation; one whole-function trampoline only when the target is fingerprinted and decisive.

## Correct custom UJ graph
User-confirmed required order:

`700 -> 707 -> 708 -> 710 -> cinematic`

Therefore P97's 707->708 suppression is retired permanently as a fix candidate.

## P98B artifact audit
Uploaded runtime artifact is structurally valid.
- paired main hash matches baseline.
- restore main hash matches baseline.
- compiled subsdk9 SHA256: `0e78233889c538a56b1675fe2522bbc2f297d9845a97c1ff487bb0f911f04657`
- runtime P98B READY observed.

## P98B decisive runtime result
During custom action708:

`[NSC:P98B] STATE_REQ ... req=125 ... caller_off=0x7EB28C ... action=708->708 ... e9c=0->125`

This proves state125 is explicitly requested while action708 is active. It is not a random state-engine side effect.

Immediately downstream:
- E94 commits to 125 / E98 becomes 63.
- BDA4 becomes 0; BDA8 becomes 1.
- PlayAction261 is requested from caller main+0x7DE558.
- action261 then falls to action74.
- no action710 request occurs in the observed custom run.

Thus action261 is downstream of the state125 branch, not the earliest root cause.

## Static correction to P98B slot labeling
P98B hooked main+0x7A89A4 correctly, but its old README label that main+0x7EB270 directly calls vslot +0xE28 was incomplete.

Pinned v1.70 chain:
1. main+0x7EB270 loads W1=125.
2. It calls actor vslot `+0xDF0`.
3. For the observed runtime vtable, +0xDF0 -> main+0x635C0C wrapper.
4. That wrapper ultimately tail-dispatches the state request through vslot `+0xE28` -> main+0x7A89A4.
5. Tail-dispatch preserves the original LR, so P98B correctly reports caller_off `0x7EB28C`.

Therefore the P98B provenance result remains valid; only the direct-slot description needed correction.

## Exact state125 producer / cleanup chain
Runtime custom vtable: main+`0x201BF58`.
Relevant pinned relocation targets:
- +0x1278 -> main+0x7EB518
- +0x12C8 -> main+0x794E74
- +0x12D0 -> main+0x794EBC
- +0x1988 -> main+0x7EB270
- +0xDF0 -> main+0x635C0C
- +0xE28 -> main+0x7A89A4
- +0xE40 -> main+0x7B468C
- +0xEB0 -> main+0x772594

Generic cleanup corridor:
- main+0x7EAF90 calls actor vslot +0x1988.
- custom +0x1988 implementation main+0x7EB270 explicitly requests state125.

Before +0x1988, the corridor evaluates vslot +0x1278 and other gates. The custom +0x1278 target is main+0x7EB518.

## E74 false lead eliminated
Vslot +0x12C8 at main+0x794E74 depends strongly on actor+E74, but existing P92 data shows E74=0 in both the custom UJ and successful vanilla UJ samples. E7C is also nonzero in both relevant action-boundary samples. E74 is therefore not sufficient to explain the divergence and must not be patched.

## Action708 state observation
Immediately after PlayAction708 commits, custom action is 708 but E94 changes from 136 to 63 before the state125 request. This is upstream of state125 and appears to be part of native action708 side effects. Do not patch E94.

## P99A design — cleanup gate +0x1278 trace
Functional parent: P96A. P97 and P98 are not installed.

P99A adds exactly one read-only trampoline:
- main+0x7EB518 (custom runtime vslot +0x1278 predicate)

Fingerprint:
`A9BE57FE A9014FF4 B94F2408 7100051F 54000120 AA0003F3 97FD9310 350000C0`

Marker:
- `[NSC:P99A] GATE1278`

Logs:
- native predicate return value
- caller provenance
- dynamic vtable +0x1278 and +0x1008 targets
- action/E94/E98/E9C/EA4/EA8/BDA4/BDA8/BDC8
- E70/E74/E7C
- actor+F24
- actor+0x106F4 and +0x10F54/+0x10F58/+0x10F60/+0x10F64

P99A also adds zero-extra topology logging through the existing PlayAction hook:
- `[NSC:P99A] TOPO`
- logs dynamic +0x1278/+0x12C8/+0x12D0/+0x1988 targets for action707/708/710.

This is important because a successful vanilla actor may use a different virtual implementation from the custom fixture; absence of a vanilla GATE1278 hit can then be interpreted using TOPO rather than guessed.

P99A performs no gameplay writes, no action rewrite, no force708/710, and no char281 gameplay branch.

## Next runtime test
In one session:
1. Vanilla character: land one successful Ultimate Jutsu through cinematic/710.
2. Custom Tobi fixture: land UJ through 707->708 and reproduce failure.
3. Upload log + compiled P99A artifact.

Decision matrix:
- Same +0x1278 implementation, different predicate return -> compare raw P99 dependencies and localize exact condition.
- Different +0x1278 implementation -> vtable/class behavior is the next structural divergence.
- Same predicate behavior but custom still state125 -> move to the +0x12C8/+0x12D0/fallback gate immediately before +0x1988.
- Custom reaches 710 -> verify cinematic completion and preserve victim Event236 behavior before moving on.
