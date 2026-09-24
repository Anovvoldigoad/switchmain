# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R97

## Baseline
- Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- exlaunch pinned `229bbd6`

## Locked architecture
- Generic/data-driven custom-character compatibility only.
- Fixture char281 must never become a gameplay hardcode.
- P89 actor-predicate bridge remains the UJ admission solution.
- P50 victim-safe/Event236 shadow behavior remains required.
- Avoid additional whole-function trampolines where possible.
- Do not force 700/708/710, E94, F58, BDA4/BDC8/EA4, selector8, or raw Event236.

## P95A runtime — decisive producer localization
P95A booted and emitted the expected read-only markers.

At the observed semantic custom failure:
- action before request: 707
- request: 708
- PlayAction caller: `0x7725D0`
- EA4=`0x258`, EA8=`0x1F4`
- BDA4=1, BDA8=0, BDC8=0
- q10600=`0x4A` (74), therefore the actor+0x10600 queued-action hypothesis is not the source.

P95A WRAPPER_PARENT for that exact request proved:
- `hit48fe4=0`
- `hit7732a8=0`
- `hit7eff8c=1`
- `e0=0x7eff8c`
- call stack also contains return `0x7eff40`.

Therefore:
1. observed 708 is NOT produced by direct sequence processor `0x48F18`;
2. observed 708 is NOT produced by the `0x7732A0` actor+0x10600 queued-action path;
3. observed 708 IS produced through the `0x7EFEBC / 0x7EFFxx` transition controller.

## Static proof after P95A
### main+0x7EFEBC transition controller
- saves actor in X19;
- `0x766A98(actor)` obtains current action from actor+0x218/+0x2C;
- `0x782C08(actor,current,0)` obtains the native action record;
- descriptor pointer is loaded from the record into X23;
- descriptor byte/string at `X23+0x94` is tested;
- if non-empty, `0x7EFF3C BL 0x3F5540` resolves that key to a numeric action ID;
- return `0x7EFF40` is present in the exact P95A failure stack;
- result becomes W21;
- `0x7EFF84 LDR X8,[X8,#0xEB0]` / `0x7EFF88 BLR X8` dispatches the resolved ID;
- actor vtable+0xEB0 resolves to generic wrapper `0x772594`.

### main+0x3F5540 / main+0x80EFEC
`0x3F5540` forwards the inline descriptor string/key into a global lookup manager.
`0x80EFEC` constructs/searches the key and returns the numeric ID from the matched
record. Thus action708 is data/name-resolved upstream of the generic wrapper.

### Action record/table path
- `0x766A98`: current action = actor+0x218 -> +0x2C (fallback 74)
- `0x769B04`: for actions 700..908, actor+E70 mode 1/2/3 maps to +84/+126/+168.
  For the observed custom fixture and vanilla comparison fixture the later
  character-specific branch does not apply; both log E70=0 in the relevant UJ.
- `0x7948E8`: table cache slot = actor+0x11660 + (actor+E90)*8
- `0x782C08`: record address = table_base + mapped_action*0x18
- relevant logs have E90=0.

## Consequence
The first bad transition is now localized to a native data-driven action
descriptor transition key, not to PlayAction, not to the +0x124xx sequence
controller, and not to actor+0x10600.

The remaining discriminator before a gameplay write is whether:
A. custom action707 descriptor itself contains a non-empty/different +0x94 key
   that resolves to 708; or
B. custom is selecting the wrong action table/descriptor before that lookup.

## P96A design
P96A is read-only and zero-extra-trampoline. It reuses P93/P95 callbacks and logs:
- current actor state/current action;
- E70/E90;
- action-table slot/object/base;
- record/descriptor for indices 707, 791, 833, 875;
- descriptor +0x6C/+0x72;
- inline key beginning at descriptor+0x94.

Markers:
- `[NSC:P96A] READY`
- `[NSC:P96A] ACTDESC`

P95A's old 0x1000 wrapper stack scan is muted in P96A because parent 0x7EFF8C
is already proven and the old scan produced emulator unmapped-page invalidation
noise near the stack mapping boundary.

## P96A runtime objective
One vanilla successful UJ plus one custom 707->708 UJ should determine whether
707 descriptor content itself differs or the selected table/descriptor is wrong.
Only then implement the smallest generic semantic-UJ compatibility write.
