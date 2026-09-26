# NSC2Switch Master Checkpoint — R135 / P120A
Date: 2026-09-26

## Locked target
- Game: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin: `229bbd6`
- final compatibility architecture remains generic/data-driven; custom char281 is fixture only.

## P119A final read-only verdict
P119A is the end of the read-only phase.

Successful control runtime:
- attacker char86 side0, action707, EA4=0x834;
- paired victim char76 side1;
- damage cursor/index126;
- `DAMAGE_ID_SPATK_BEGIN_DIRECT`;
- raw10;
- `gate10=1`;
- pair_ok=1, trace_gap=1.

Custom runtime:
- attacker char281 side0, semantic=1, action707;
- EA4=0x190 -> victim char27 cursor/index1848 -> raw15 -> `DMG_MTOB_SPL01` -> gate10=0;
- EA4=0x1F4 -> victim cursor/index1847 -> raw24 -> `DMG_MTOB_SPL00` -> gate10=0;
- pair_ok=1, trace_gap=1 on both;
- natural 707->708 follows at EA4=0x258 through caller 0x7725D0.

This proves the observed bucket5 cinematic divergence is the damage classification presented to the victim gate, not B9E4 corruption. P118B already proved idx1847/1848 are coherent appended records in the 1849-record loaded table.

## Corrections locked
- X19 at bucket5 is victim-owned; do not call raw15/raw24 the attacker's event cursor.
- Do not revisit wrong-cursor/B9E4 as root without contradictory evidence.
- Do not suppress natural 707->708 (P97 control failed).
- Do not force action710, state137, type9/type10 sessions, or directly create sessions.
- Do not globally mutate custom damage records to raw10.
- 0x77C474/0x77C5E8 is one proven cinematic corridor, not a universal corridor for all characters.

## P120A corrective A/B
P120A installs exactly one additional inline hook at `main+0x77C474`, the boot-proven P115B site.
Original instruction:
`LDR W8,[X20,#0x50]`

Callback always replays the native load. W8 is overlaid to 10 only when:
1. record belongs to appended custom damage range (`idx>=1847 && idx<count` on locked v1.70);
2. coherent latest attacker snapshot exists;
3. attacker is generic custom ID `>280 && <0x1000`;
4. semantic-UJ is true;
5. attacker action is exactly 707;
6. victim is valid and opposite side;
7. P93 trace gap <=16;
8. native raw does not already pass `(raw&~1)==10`;
9. attacker has not already been bridged during current action707.

The latch is plugin-local and resets once the attacker leaves action707.

No char281 or DMG_MTOB name branch. No event record/B9E4/damage-table/session/action/state write. No force708/710.

## Interpretation of next hardware run
- `bridge=1` + cinematic succeeds: causal support that this compatibility gap is the missing custom semantic cinematic classification at the proven bucket5 gate. Continue regression/tightening, not more read-only exploration.
- `bridge=1` + cinematic still fails: the patch has newly opened the downstream gate; inspect newly reached C48/type9/0x7EF098 path. Do not go back upstream to cursor/damage index.
- no `bridge=1`: diagnose guard mismatch from P120 GATE/context, not session forcing.
