# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R96

## Baseline
- Storm Connections Switch v1.70.
- Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`.
- Generic/data-driven compatibility only; fixture char281 is never a gameplay hardcode.
- Paired main remains SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`.
- Restore main remains SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- exlaunch pinned at `229bbd6`.

## P94A runtime result — hypothesis falsified
- P94A booted read-only / zero-extra-trampoline.
- Vanilla successful UJ still reaches native 710 from caller `0x7E6EC8` even though P94A reports the `+0x12470/+0x124A0/+0x124D0` vectors invalid.
- Custom semantic UJ still leaves 707 at `EA4=0x258`, requests 708 from `0x7725D0`, while the same three vectors are invalid and `idx1246C` is not a usable active sequence index.
- Therefore observed custom 707->708 is not proven to be produced by `0x48F18` / actor `+0x12460` sequence family.

## Static correction after P94A
- `0x772594` is not reachable only by direct BL.
- It is used as a virtual-dispatch target through actor vtable slot `+0xEB0`.
- Concrete path near `0x7732A0`:
  - W1 is loaded from `[x21+0x124]`.
  - x21 is actor+`0x104DC` in this controller.
  - therefore W1 source is actor+`0x10600`.
  - virtual call returns at `0x7732A8`.
  - after success the controller resets actor+`0x10600` to action74.
- Alternate vtable+`0xEB0` path calls at `0x7EFF88` and returns at `0x7EFF8C`; its W1 is helper-selected rather than loaded from actor+`0x10600`.
- Direct `0x48FE0 -> 0x772594` path remains possible in general, returning at `0x48FE4`.

## P95A design
P95A remains read-only and zero-extra-trampoline and reuses all existing hooks.

### QUEUECTRL
Logs during existing P93 UJ-state observations:
- actor+`0x104DC`, `+0x104E0`
- actor+`0x105E8`, `+0x105EC`, `+0x105F0`
- actor+`0x105F4`, `+0x105F8`, `+0x105FC`, `+0x10600`
- actor+`0x10604`, `+0x10608`, `+0x1060C`, `+0x10610`
- actor vtable+`0xEB0` target and main-relative offset.

### WRAPPER_PARENT
When existing PlayAction observes UJ action from caller `0x7725D0`:
- SP is captured at callback entry before helper calls.
- stack is scanned read-only for main-relative BL/BLR return addresses.
- explicit flags identify `0x48FE4`, `0x7732A8`, and `0x7EFF8C`.
- generic call candidates and vtable+EB0 call-return candidates are retained in the same log line.

## P95A objective
One runtime pair (vanilla successful UJ + custom 707->708) should determine:
1. whether actor+`0x10600` is 708 before the observed wrapper call;
2. whether the wrapper parent is `0x7732A8`, `0x7EFF8C`, `0x48FE4`, or another indirect callsite;
3. which nearby queue/controller words diverge before custom leaves 707;
4. whether the vtable+`0xEB0` target is the expected generic `0x772594` wrapper for both actors.

Do not suppress 708 or force710 until P95A identifies the actual producer class.
