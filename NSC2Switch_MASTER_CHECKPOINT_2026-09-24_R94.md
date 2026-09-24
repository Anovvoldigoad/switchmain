# NSC2Switch MASTER CHECKPOINT — R94 / P93A
Date: 2026-09-24

## Locked baseline
- Switch v1.70 Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
- Paired main SHA256: 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
- Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
- exlaunch pinned: 229bbd6
- P89 admission bridge remains functional parent. No raw Event236 native restore.

## Proven P92 runtime frontier
- Custom fixture reaches 700 -> 707 and then requests 708 at caller 0x7725D0 / callsite 0x7725CC.
- Successful vanilla reaches 700 -> 707 and then requests 710 at caller 0x7E6EC8 / callsite 0x7E6EC4.
- At 707 boundary custom and vanilla share E94=136, E98=135, E9C=0, EA0=0, EA4=0xFFFFFF9C.
- P92 observed E6C/E70 differences, but source provenance already defines E68/E6C/E70 as skill0/skill1/skill2. Therefore E6C/E70 are loadout data, not a generic handoff root candidate; do not force them.
- E90 remains an unknown discriminant and is traced, but no write is justified.

## P93A design
Goal: maximize temporal visibility without adding trampoline pressure.
- ZERO new hook/trampoline installation.
- Read-only CORE snapshots emitted from hooks already installed by the proven P89/P92 parent chain.
- Tags: PLAYACTION, CENTRAL_SETTER, MODE_BASE, P81_POLICY, P77_UJ_ACCEPT, P88B_HELPER, P89_ACTOR_PRED, EVT236_PRE.
- CORE captures action; E40/E44/E48/E4C/E50/E54; E60/E64/E68/E6C/E70/E7C/E80/E84/E88/E8C/E90/E94/E98/E9C/EA0/EA4/EA8/EAC; BDA4/BDA8/BDC8; 106F4/123E0/123E4; 7CC; control+404/+408/+5A0.
- Trace condition: player-side or custom actor, and semantic UJ or UJ-like action/state.
- Hard cap: 65536 CORE records.

## Safety / forbidden shortcuts
- no char==281 gameplay branch
- no force 708/710
- no E6C/E70 skill-slot copying
- no E90 write
- no BDA4/BDC8/EA4 write
- no selector8 mapping
- no 445->700 rewrite
- no new trampoline

## Next runtime comparison
Run a successful vanilla UJ and the custom Kamui failure in the same boot. Compare the P93 CORE timeline and identify the earliest tag/state at which the paths diverge before 0x7725CC vs 0x7E6EC4. Only after a producer/predicate is proven should a generic preserve-native bridge be considered.
