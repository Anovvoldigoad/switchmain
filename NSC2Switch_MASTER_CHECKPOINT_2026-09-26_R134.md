# NSC2Switch Master Checkpoint — R134 / P119A

## Locked target
- Game: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pinned commit: `229bbd6`
- Custom Tobi remains fixture only; compatibility must stay generic/data-driven.

## Preserved baseline
- P50 victim-safe Event236 shadows remain required.
- P89 generic semantic/membership admission bridge remains required.
- P97 suppression of 707->708 is retired; natural 708 must remain.
- No force708/710, no E9C/state137/session writes, no char281 gameplay branch.

## P116 / P117 locked downstream proof
- Successful vanilla UJ creates cinematic session through `main+0x7EF098`.
- Custom Tobi executes 700->707->708 but does not reach the cinematic outer call.
- Therefore session9/session10, manager/state137 and native710 are downstream consequences, not roots.

## P118B correction — ownership was previously misattributed
P118B validated direct cursor and event-record pointer identity, and proved that X19 / `[actor+0xB9E4]` at bucket5 is the VICTIM actor being processed.

Successful control sample:
- attacker side0 is in action707;
- victim side1 selects cursor126 `DAMAGE_ID_SPATK_BEGIN_DIRECT`;
- raw type = 10, mask48 = 0x4000;
- cursor pointer identity is exact;
- cinematic bucket5 gate therefore passes.

Custom Tobi sample:
- attacker side0 char281 is in action707;
- victim side1 selects cursor1848 `DMG_MTOB_SPL01`, raw15, end_delta=0;
- then cursor1847 `DMG_MTOB_SPL00`, raw24, end_delta=1;
- pointer-derived indices match direct cursor values;
- then Tobi performs natural 707->708 through caller `0x7725D0`.

The global damage table has count1849. Historical compiler reconstruction already proved vanilla=1847 + exactly two Tobi records, `DMG_MTOB_SPL00` and `DMG_MTOB_SPL01`. Runtime indices 1847/1848 therefore match the appended Tobi records exactly. Wrong/out-of-range B9E4 is not supported as the root.

## Source-event cross-check
Recovered Tobi source events contain multiple SPSKILL families inside the same source chunk. Critically:
- one `PL_ANM_SPSKILL_1_START` family contains event209 `DAMAGE_ID_SPATK_BEGIN_DIRECT`;
- another `PL_ANM_SPSKILL_1_START` family contains repeated `DMG_MTOB_SPL00` and `DMG_MTOB_SPL01` damage events;
- runtime custom behavior matches the SPL family.
This is correlation, not yet proof of the exact upstream selector bug.

## Current state-of-truth
```
ATTACKER UJ producer
      |
      v
selects damage/event family
      |
      +-- successful control -> DAMAGE_ID_SPATK_BEGIN_DIRECT -> victim raw10 -> bucket5 PASS
      |
      +-- current Tobi     -> DMG_MTOB_SPL01/SPL00          -> victim raw15/raw24 -> bucket5 FAIL
                                                                 |
                                                                 +-> no 0x7EF098
                                                                     no cinematic session
                                                                     no native137/710
```

## P119A purpose — FINAL read-only provenance
P119A reuses the already boot-safe P118B hook at `main+0x3F4BC0` and adds no second trampoline. Existing P93 callbacks publish the latest coherent side0 UJ producer snapshot. At each victim bucket5 damage record, P119A emits a correlated pair:
- `[NSC:P119A] LINK`: attacker pointer/char/action/semantic/e44/e94/e98/e9c/EA4 + trace gap;
- `[NSC:P119A] DAMAGE`: victim pointer/char/action + cursor/index/raw + cinematic gate result + exact damage name.

A small seqlock protects diagnostic snapshot coherence. `trace_gap <= 16` prevents stale UJ producer pairing. All writes are to subsdk9 diagnostic atomics only; gameplay actor/event/session memory remains untouched.

## Interpretation gate
1. Control shows gate10=1 and Tobi paired window shows no gate10=1: stop read-only work and implement the first generic corrective patch at the upstream SPSKILL/damage-event selection producer.
2. Tobi shows gate10=1 but still no cinematic: contradiction with current downstream model; audit that exact row before patching.
3. Any cursor/index mismatch or stale pair: instrumentation-invalid run; do not infer gameplay root.

## Explicitly retired directions
- victim125/126 as universal root;
- type9/type10 session creation as root;
- manager/state137 as root;
- force710 / force137 / force session;
- suppressing natural 708;
- treating P118 global +/-32 neighborhood as a logical action-block boundary;
- treating raw10/raw15/raw24 as attacker-owned action707 event stream.
