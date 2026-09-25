# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R120

## Locked target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## Required custom UJ graph
`700 -> 707 -> 708 -> 710 -> cinematic`

Action708 is legitimate and remains mandatory. P50 victim-safe Event236 shadows and P89 generic admission remain locked.

## P108A compiled/runtime audit
Uploaded compiled artifact:
`NSC-P108A-post708-state136-lifecycle-bridge.zip`

Artifact integrity/manifest passed. Deployed paired/restore main fingerprints are correct; compiled `subsdk9` SHA256 is `dcdad54f8900dfae979bf820a50c69c7ca54a4a35e0ef798f8545e4f0ac1f858`.

User-visible result:
- victim UJ remains safe; Tobi does not disappear;
- Tobi own UJ has no cinematic;
- Kamui absorb starts, Tobi turns/replays, enemy remains in absorb behavior;
- Tobi becomes uncontrollable.

## P108A decisive runtime result — RETIRED
P108A bridge fires on the exact intended custom fingerprint:
- action708;
- E94=63, E98=136, E9C=0;
- BDA4/BDA8/BDC8=1/0/0;
- caller return `0x7EB28C`;
- native request125 is mapped to136 through `main+0x7A89A4`.

But after state136 commits, controller `main+0x7E47B8` enters its mode0 beginning and calls PlayAction707 at `0x7E4858`, return `0x7E485C`.

Therefore actual P108 sequence is:

`700 -> 707 -> 708 -> map125to136 -> commit state136 -> 707`

This is backwards. It directly explains the visible post-absorb replay/turn/stuck behavior. P108A is retired and must not be extended.

## Static correction
The actions 136/138/137 observed around `main+0x7E5480` are participant setup actions inside the state136 controller. They are not evidence that the main actor should be re-entered into state136 after action708.

State table/controller mapping remains factual:
- state125 -> vslot +0x4C0 -> `0x7DDD94`;
- state136 -> vslot +0x518 -> `0x7E47B8`;
- state137 -> vslot +0x520 -> `0x7E64D4`.

But P108 proves that state136 is not a valid post-708 bridge target at the cleanup request point.

## Same-session vanilla UJ control — new decisive frontier
The P108 runtime log also contains a successful vanilla side0 char276 UJ in the same boot.

Immediately before state137 handoff, vanilla remains action707 / E94=136 / E98=135:
1. `EA4=0x708`, `EA8=0x6A4`, `E9C=0`, `BDA4=0`, `BDA8=1`.
2. Roughly one tick later: `EA4=0x76C`, `EA8=0x708`, `E9C=137`, `BDA4=0`, `BDA8=0`.
3. state137 commits: E94=137 / E98=136 / E9C=0.
4. `main+0x7E6EC4` calls PlayAction710 and returns at `0x7E6EC8`.

This is now the exact native handoff maturation to localize.

## P109A design — READ ONLY state137 provenance
Functional parent returns to P96. P107/P108 functional mappings are absent.

P109A installs exactly one whole-function trampoline at the proven base state-request gateway:
- `main+0x7A89A4`.

It logs only requested states:
- 125
- 136
- 137

For each focused call it logs:
- caller LR/main offset;
- actor/side/char;
- req/arg2/arg3;
- action, E94/E98/E9C pre/post;
- EA4/EA8 pre/post;
- BDA4/BDA8/BDC8 pre/post;
- dynamic vtable +0xE28 target;
- native return.

The original function is called with unchanged request/arguments/result. No mapping and no gameplay write occurs.

P109 also fingerprints, but does not hook, the direct/simple E9C writer:
- `main+0x7A8A9C`: `STR W1,[X0,#0xE9C]`, followed by EB0 arming.

## P109A decision matrix
Run in this order in one fresh session:
1. one successful vanilla UJ through 710;
2. one failing custom Tobi UJ through 708 -> natural cleanup;
3. victim-UJ regression only if convenient (P109 itself is read-only).

Interpretation:
- vanilla `P109 STATE_REQ req=137` exists -> caller_off is the exact native state137 producer; probe/compare only that producer next;
- vanilla trace shows E9C=137 but P109 has no vanilla req137 -> state137 bypasses `0x7A89A4`; next target is `main+0x7A8A9C` family;
- custom naturally has req137 -> compare caller/args/state with vanilla before any functional patch.

## Non-goals
Do not port opcode26 audio, restore op12 visibility, or restore old op14 control in P109. Those are separate parity gaps. First localize the native 707/state136 -> state137 handoff producer without another speculative bridge.
