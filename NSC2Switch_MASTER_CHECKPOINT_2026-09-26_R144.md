# NSC2Switch MASTER CHECKPOINT — R144 / P128A
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: `0100FA10190A0000`
Build ID main: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
Restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
exlaunch pin: `229bbd6`

## Locked runtime through P127
- P107 proved state137 -> native PlayAction710/cinematic works for the custom actor, but direct cleanup125->137 skips session setup and breaks lifecycle.
- P113 proved successful vanilla calls native outer setup `0x77C5E8 -> 0x7EF098`, creating type9/type10; failing custom had zero outer setup.
- P119/P120 found appended custom victim damage records: idx1848 raw15 and idx1847 raw24; P124/P125 still log the first event as raw15 with callback `out=10`.
- P123 callback-side replay of native C48/type9/lookup calls caused vanilla regression and is retired.
- P127 runtime: Naruto own-UJ safe; Tobi victim-UJ safe; Tobi own-UJ still stuck/no cinematic.
- P127 artifact audit proves paired main contains all four downstream A/B branch openings and native calls unchanged.
- Despite that, custom runtime still emits only `P124 GATE raw15 -> out10`, no downstream/post-outer marker, and later `P125 CLEANUP session=0 mature=0`.

## Corrected frontier
The remaining unproven assumption is the callback register overlay at `0x77C474`.
The log value `out=10` proves callback intent, but not that the native `AND/CMP/B.NE`
sequence consumed W8=10. P128 therefore makes gate admission static and exact enough
for this fixture class instead of relying on the callback register mutation.

## P128A static precise gate cave
Paired main SHA256: `904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff`.

- `0x77C480`: native B.NE reject -> unconditional B `0x77C4B8` cave.
- Cave preserves raw10/raw11 native admission.
- Cave admits raw15 only when attacker char id is generic-custom (`>280 && <0x1000`) and current action is707.
- All other raw values, including raw24, branch to native reject `0x77C5F0`.
- Accepted traffic branches back to native actor-C48 entry `0x77C484`.
- The cave occupies the old `0x77C4B8..0x77C500` block, which P127's `0x77C4B4 -> 0x77C514` makes unreachable from normal type9 flow.

P127 downstream A/B remains:
- actor reject `0x77C494` NOP;
- peer reject `0x77C4A8` NOP;
- type9 result `0x77C4B4 -> 0x77C514`;
- lookup result `0x77C520 -> 0x77C59C`;
- all native C48/type9/lookup/0x7EF098 calls preserved once from main.

## P128 runtime proof chain
Active diagnostic hooks are reduced to:
1. P124 gate strict arm/log.
2. P128 post-outer at `0x77C5EC`, using a persistent P128 actor latch not cleared by transient action changes.
3. P125 cleanup session-qualified/mature-context-qualified state137 fallback.

P128 READY logs actual runtime words at the gate/cave/downstream sites, proving the
paired main really loaded in the emulator.

## Decision
- READY runtime words mismatch -> deployment/LayeredExeFS problem.
- READY matches, GATE raw15, POST_OUTER ret=1 -> native session setup reached; inspect whether native manager now emits137/710 before using P125 fallback.
- READY matches, GATE raw15, no POST_OUTER -> divergence/non-return lies inside native helper corridor after gate; do not revisit B9E4/raw classification/session137 forcing.

## Invariants
P50 victim-safe shadows and P89 generic admission preserved. No char281 branch,
no direct 0x7EF098 call, no callback-side native-call replay, no force708/710, no
game-memory field write.
