# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R95

## Baseline / fingerprints
- Title: Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- exlaunch pinned: `229bbd6`

## Locked architecture
- Generic/data-driven custom-character compatibility only; fixture char281 must never become a gameplay hardcode.
- P89 actor-predicate bridge solved UJ admission generically.
- P50 victim-safe/Event236 shadow behavior remains required.
- P90A proved trampoline pool is exhausted enough that two extra whole-function trampolines can fail boot. Prefer zero-extra instrumentation.
- Do not force action700/708/710, E94, F58, BDA4/BDC8/EA4, selector8, or raw native Event236.

## P93 runtime — decisive post-707 timing result
### Vanilla successful UJ
At action707, native actor remains in:
- E94=136, E9C=0
- BDA4=1, BDA8=0, BDC8=0
- EA4 advances by 0x64 per observed tick.

Immediately before successful 710, native handoff-arm state appears:
- E9C=137 (`0x89`)
- EA4=`0xAF0`, EA8=`0xA8C`
- BDA4=0, BDA8=1, BDC8=0
Then PlayAction710 occurs from caller `0x7E6EC8`.

### Custom semantic UJ fixture
After 700->707, custom remains:
- E94=136, E9C=0
- BDA4=1, BDA8=0, BDC8=0
- EA4 progresses only to `0x258` before leaving 707.
At that point it requests action708 from caller `0x7725D0` and never reaches the native handoff-arm state above.

### Consequence
The first actionable divergence is not admission and not PlayAction710 itself. Custom exits 707 prematurely before native handoff-arm maturation.

## Static proof after P93
### Generic 0x772594 wrapper
- `0x772594` rejects action74 specially, otherwise forwards its incoming W1.
- `0x7725CC BL 0x766B8C` calls PlayAction with W1 already selected.
- The wrapper itself does NOT choose action708.
- Therefore globally patching `0x7725CC/0x7725D0` is invalid.

### Sole direct caller and sequence producer
Direct BL scan found one direct xref to `0x772594`:
- `0x48FE0 BL 0x772594` inside function `0x48F18`.

`0x48F18` is a data-driven action-sequence processor:
- uses actor+`0x1246C` as current sequence index;
- reads an action ID from a begin/end vector passed in X1;
- validates it through native helpers;
- calls `0x772594(actor, action)`;
- advances the sequence index after success.

Caller/controller analysis shows actor-owned vector/controller families:
- controller/pointer `+0x12460`
- state/counter `+0x12468`
- current index `+0x1246C`
- vector `+0x12470`
- vector `+0x124A0`
- vector `+0x124D0`
- flag `+0x12500`
- mode `+0x12504`

Therefore custom action708 is strongly localized to an actor-owned runtime action sequence, not a 281-specific branch at PlayAction.

### 710 corridor
- `0x7E6EA8` materializes action710; `0x7E6EC4` calls PlayAction.
- An alternate path checks a context flag and whole-function predicate `0x7E8E2C` before proceeding.
- Static analysis of `0x7E8E2C` shows target/opponent/action/timing checks plus actor field `+0x12320`.
- Treat it as a candidate handoff predicate, not yet a proven root cause.

## P94A design
P94A remains read-only and zero-extra-trampoline. It reuses P93's existing callback sites and logs:
- actor+`0x12320`
- actor+`0x12460`, `0x12468`, `0x1246C`
- actor+`0x12500`, `0x12504`
- raw begin/end/cap/count for vectors at `+0x12470`, `+0x124A0`, `+0x124D0`
- first six action IDs plus prev/current/next element around current index.

Markers:
- `[NSC:P94A] READY`
- `[NSC:P94A] SEQCTRL`
- `[NSC:P94A] SEQVEC`

## P94A runtime objective
Compare vanilla successful 707 maturation with custom 707->708 and determine:
1. which vector is active;
2. whether 708 is literally a sequence item for the custom runtime path;
3. current index/mode when 708 is consumed;
4. whether the native 710 handoff is being pre-empted by the sequence processor;
5. whether actor+0x12320 differs before the 710 timing predicate.

Only after this proof should a generic compatibility bridge be designed. Do not suppress 708 or force710 speculatively.
