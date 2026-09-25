# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R121

## Locked target
- Storm Connections Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## P109A runtime result — decisive
P109A was read-only and successfully localized native state137 provenance.

Same-session vanilla char276:
- request136: caller return `main+0x7E3778`, action700, E9C `0 -> 136`;
- state136 produces action707;
- later request137: caller return `main+0x74FF7C`, action707, E94=136/E98=135, E9C `0 -> 137`, BDA4=0/BDA8=0;
- state137 commits, then native PlayAction710 is produced at caller `main+0x7E6EC8`.

Same-session custom Tobi:
- request136: same caller `main+0x7E3778`, action700;
- reaches state136/action707;
- legitimate custom transition `707 -> 708` at caller `main+0x7725D0`;
- no request137 appears;
- cleanup request125 occurs at caller `main+0x7EB28C`, action708, E94=63/E98=136/BDA4=1;
- then native fallback `708 -> 261 -> 74`.

Therefore admission and initial state136 entry are no longer suspect. The missing transition is between custom action708 and the cinematic-session manager handoff that normally emits state137.

## P107 / P108 retired
P107 mapped cleanup125 directly to137. It caused native 710/cinematic entry but skipped native cinematic-session setup, leaving broken own-UJ lifecycle.

P108 mapped cleanup125 to136. Runtime proved that state136 re-entry immediately replays PlayAction707 from `main+0x7E485C`, producing the visible Kamui replay/reversal/stuck behavior.

Do not reuse either mapping.

## Static provenance of native req137
The P109 caller `main+0x74FF7C` lies inside function `main+0x74F954`.

Unique direct caller:
- `main+0x74F6AC -> main+0x74F954`;
- dispatcher only calls it for an entry whose type field is `10`.

The function uses `ctx+0x04` as a phase index with native phase cases 0..5.

### Phase2 gate
At `main+0x74FA9C`:
- resolve paired actor from leader via `main+0x796384`;
- if paired exists, read a value through `main+0x796BEC`;
- `main+0x796BEC` is a simple getter for `*(uint32_t*)*(actor+0xB968)` (0 when pointer is null);
- compare to 1;
- value `>1` returns/stays waiting;
- value `<=1` advances manager phase to3.

### Phase3
Phase3 begins at `main+0x74FAFC` and performs substantial leader/paired/session setup before the native state137 request.
At `main+0x74FF54...0x74FF78`, the manager resolves the leader actor and requests state137; LR after the BLR is exactly `main+0x74FF7C` as proven by P109.
It then requests state81 for the paired actor and advances manager phase 3 -> 4.

This proves P107 skipped the manager phase3 lifecycle, while P108 re-entered the actor state machine rather than this session manager.

## P110A design — read-only manager phase provenance
Functional parent returns to P96. P109/P108/P107 functional/diagnostic hooks are not installed.

Exactly one new trampoline:
- `main+0x74F954`.

Captured per invocation:
- manager phase pre/post and previous phase;
- manager team/flag/timer fields;
- resolved leader actor identity/action/E94/E98/E9C/BDA fields;
- resolved paired actor identity/action/E94/E98/E9C/BDA fields;
- paired `+0xB968` pointer/value, dereferenced only during pre-phase2 where native code uses that gate.

No gameplay state is modified. Native arguments and return are preserved.

## P110A decision matrix
- Vanilla reaches phase2 -> phase3 with paired B968 <=1: establishes control signature.
- Custom has no manager rows: missing type10 session creation/registration upstream.
- Custom repeats phase2 with B968 >1: exact root frontier is paired actor B968 readiness.
- Custom has B968 <=1 but phase2 does not advance: inspect lookup/manager context around `0x74FA9C`.
- Custom reaches phase3 but no state137: inspect phase3 setup before `0x74FF6C`.

## Protected baseline
- P50 victim-UJ safe Event236 shadows remain mandatory.
- P89 generic UJ admission bridge remains inherited through P96.
- Do not reopen HOLD125/HOLD74, `0x7EE8E0`, `+0x12240`, P107 or P108 without contradictory evidence.
