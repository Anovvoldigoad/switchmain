# NSC2Switch MASTER CHECKPOINT — 2026-09-26 — R133

## Locked target
- Game: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pinned commit: `229bbd6`

## Preserved functional baseline
- P50 victim-safe Event236 shadows remain required.
- P89 generic semantic + membership admission bridge remains required.
- Custom Tobi is generated char281 in current fixture, but runtime fix logic must remain generic/data-driven.
- Action708 is a legitimate native transition and MUST NOT be suppressed absent new proof.
- No force state/action/session workaround.

## Locked upstream boundary
P116 established that successful cinematic execution reaches `main+0x7EF098`, while
failing custom Tobi never calls it. Session9/session10, manager137 and action710 are
therefore downstream symptoms, not the current root frontier.

## P117 locked runtime divergence
Successful vanilla/control action707 dispatches type10/11-family event data.
Custom action707 dispatches raw15 then raw24 and does not dispatch type10/11 before
its natural 707->708 transition.

## P118A current run — corrected interpretation
Current P118A run:
- control char111: action700 -> 707; selected idx124 raw11/norm10; later reaches 710;
- custom char281: action700 -> 707; idx1848 raw15 then idx1847 raw24; natural 708 from `0x7725D0`; no 710;
- custom samples report no type10/11 in the sampled +/-32 GLOBAL record radius.

Correction to R132 decision language:
- +/-32 is not a proven logical action block boundary;
- `near10_delta=127` proves only no type10/11 was found in that radius;
- nearby type10/11 would not prove wrong cursor until same logical block ownership is established.

## Static v1.70 proof added for R133
Dispatcher `main+0x77B560`:
- `0x77B588 MOV X19,X0` => X19 = actor;
- `0x77B58C LDRH W0,[X0,#0xB9E4]` => direct actor event cursor;
- `0x77B590 BL 0x3F4B00` => event record lookup;
- X19 is not overwritten before `0x77B5A8 BL 0x3F4BC0`.

Global event container used by `0x3F4B00`:
- root pointer slot `main+0x2143488`;
- chain `root -> +0x6C10 -> +0xB8` => container;
- container+0x48 = event records base;
- container+0x50 = event record count;
- record stride = 0x60.

`main+0x3F4B60` uses the same count and container+0x58 with stride 0x30 to return
the matching event-name string for an index. Native v1.70 has one direct caller at
`0x77BFE8`.

## P118B experiment
P118B remains read-only and retains the single boot-safe trampoline at `0x3F4BC0`.
It captures live X19 immediately, reads direct `[actor+0xB9E4]`, validates it against
pointer-derived index/event pointer, logs count/end-distance/global A8-AA-AC, and dumps
+/-32 records with event names and stable fields.

### P118B decisions
1. If `cursor_ptr_match=0` or `event_ptr_match=0`: audit native state/instrumentation before any causal conclusion.
2. If custom cursor is at/near global table end: table-edge fact becomes proven, but it still does not prove cursor is wrong.
3. Compare control/custom event names and neighboring record families. A systematic family difference strengthens event-block/data-selection back-slice.
4. Only trace producer/writes of `[actor+0xB9E4]` after proving a type10/11 record belongs to the same logical action707 block and should have been visited.

## Retired / do not reopen
- victim state125/126 root theories;
- cinematic manager/state137 as root;
- type9 blocker / type10 session creation as root;
- bucket5 single caller as universal producer model;
- suppress707->708 / suppress708;
- force708 / force710 / force137 / direct session creation;
- char281-specific compatibility branches.

## Active frontier
`action707 descriptor/mapping/data selection -> selected event family/block -> direct cursor`.
P118B is designed to distinguish table/cursor identity from event-family selection before
any new behavior-changing patch is considered.
