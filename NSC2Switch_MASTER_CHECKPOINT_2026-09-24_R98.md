# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R98

## Baseline / fingerprints
- Title: Storm Connections Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- exlaunch pinned: `229bbd6`

## Locked architecture
- Generic/data-driven custom-character compatibility only. Fixture char281 must never become gameplay hardcode.
- P89 actor-predicate bridge remains the functional admission parent.
- P50 victim-safe/Event236 shadow behavior remains required.
- Do not force 700/708/710, E94, F58, BDA4/BDC8/EA4, selector8, or raw native Event236.

## P95 result — exact producer family
- Failing semantic custom 707->708 enters generic wrapper `0x772594` from virtual call return `0x7EFF8C`.
- It is NOT from direct sequence path `0x48FE4` and NOT from queued `actor+0x10600` path `0x7732A8`.
- Stack provenance also contained `0x7EFF40`, localizing the non-empty descriptor-key branch inside function `0x7EFEBC`.

## P96 runtime discriminator — decisive
### Vanilla successful fixture (char129)
At action707:
- `E70=0`, `E90=0`, mapped action = 707.
- descriptor707 exists but `d6c=0`, `d72=0`, `d94=0`, `key707=''`.
- actor later reaches native PlayAction710 from `0x7E6EC8`.

### Semantic custom fixture (char281)
At action707:
- `E70=0`, `E90=0`, mapped action = 707.
- descriptor707: `d6c=0`, `d72=2`, `d94=80` (`'P'`).
- `key707='PL_ANM_SPSKILL_1_LOOP'`.
- At `EA4=0x258`, `BDA4=1`, `BDA8=0`, `BDC8=0`, `E94=136`, `E9C=0`, native selector resolves the descriptor key and requests PlayAction708 through wrapper caller `0x7725D0`.
- Custom never reaches PlayAction710 in the observed run.

## Static proof — main+0x7EFEBC transition selector
Function `0x7EFEBC`:
1. resolves current action and descriptor;
2. checks descriptor `+0x6C` eligibility;
3. if descriptor `+0x94` is non-empty, calls resolver at `0x3F5540`;
4. resolver result becomes W21 action ID;
5. calls actor virtual slot `+0xEB0` at `0x7EFF88`; runtime slot resolves to wrapper `0x772594`;
6. native no-transition/early-return result is `0`; successful transition path returns `1`.

Therefore the direct cause of the observed premature 707 exit is a descriptor-key-driven transition that runs before native cinematic handoff maturation. This is not a global action708 problem and not a PlayAction selector bug.

## P97A functional candidate — early transition guard
P97A adds exactly one whole-function trampoline at `0x7EFEBC` and keeps P89 as functional parent.

It returns native no-transition value `0` only when ALL are true:
- semantic selector1 latch active;
- actor is present in data-driven `ougiAwakening` membership;
- current action is 707;
- `E70=0` and descriptor707 has a non-empty `+0x94` key;
- `E94=136`, `E9C=0`;
- `BDA4=1`, `BDA8=0`, `BDC8=0`.

Otherwise it calls native `Orig()` unchanged.

P97A does NOT:
- hardcode char281;
- rewrite action708;
- force action710;
- mutate E94/E9C/BDA4/BDC8/EA4;
- alter Event236/victim handling;
- change paired main.

Markers:
- `[NSC:P97A] READY`
- `[NSC:P97A] GUARD`

## P97A expected runtime proof
### Vanilla UJ
- no `guard=1`;
- native 707->710/cinematic unchanged.

### Semantic custom UJ
- while in early 707 state, `[NSC:P97A] GUARD ... guard=1`;
- no PlayAction708 from caller `0x7725D0` during that protected window;
- 707 should remain alive long enough for native handoff state to mature and request PlayAction710 from `0x7E6EC8`.

If custom reaches 710 but cinematic still does not complete, the next fault is downstream of the now-proven transition blocker. Do not re-enable the 708 path.

If P97A fails to boot before READY, classify as trampoline-capacity failure first. P90A previously proved that two extra whole-function trampolines can exhaust the trampoline pool; P97A adds exactly one.

## Runtime test order
1. Boot/menu/battle sanity.
2. Vanilla successful UJ.
3. Custom semantic UJ reproducer.
4. If own UJ reaches cinematic, custom as victim of vanilla UJ (P50/Event236 regression).
5. One ordinary custom jutsu/action transition regression.
6. Only then move to D-pad, sound, and remaining consumer-param ports.
