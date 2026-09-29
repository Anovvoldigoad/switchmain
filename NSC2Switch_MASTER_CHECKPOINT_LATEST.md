# NSC2Switch MASTER CHECKPOINT — 2026-09-29 — R176 FULL

## Baseline / frozen
- Game: NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Title ID: 0100FA10190A0000
- Build ID: 48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39
- Original main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
- Original-main runtime architecture + dynamic resolver 7/7 retained.
- Exact 30-word runtime patch retained.
- P128 retained.
- R164 StageInfo hardware PASS retained.
- R172 UJ opcode23 SetAnmDirect-equivalent parity retained.
- R171 remains retired.
- Voice remains frozen/skipped.
- Non-UJ opcode23 remains V2H safe-suppressed.

## D-pad hardware proof

### log16 = LEFT
R175 marker:
- selector primary/fallback = 2
- active_mode = 2
- base_candidate = 921
- actual PlayAction = 921
- fallback921_suspect = 0

Lookup matrix:
- 921: present for flag=1 and flag=0
- 922: NULL for flag=1 and flag=0
- 923: present for flag=1 and flag=0
- 924: present for flag=1 and flag=0
- candidate921 present
- native_candidate_missing = 0
- state_changed = 0

### log17 = RIGHT
R175 marker:
- selector primary/fallback = 3
- active_mode = 3
- base_candidate = 922
- actual PlayAction = 921
- fallback921_suspect = 1

Lookup matrix:
- 921: present
- 922: NULL for flag=1 and flag=0
- 923: present
- 924: present
- candidate_f1 = NULL
- candidate_f0 = NULL
- native_candidate_missing = 1
- flag1_only_gap = 0
- state_changed = 0

## Current root boundary
Direction routing is proven correct:
- LEFT -> mode2 -> candidate921 -> available -> PlayAction921
- RIGHT -> mode3 -> candidate922 -> unavailable -> native fallback PlayAction921

Therefore:
- retire "Left/Right selector collapse" hypothesis.
- retire "flag=1 remap-only gap" hypothesis for 922, because flag=0 also returns NULL.
- do not force PlayAction(922) while descriptor lookup is NULL.
- current target is action/animation registry parity for candidate922.

## Static proof
main+0x768E84:
- optional remap through main+0x769B04 when flag != 0;
- then loads actor+0x218;
- passes resolved index to underlying action/animation lookup.
Thus R175's NULL is actor-local action/animation availability failure, not merely a log artifact.

Native D-pad candidate table remains:
- mode0 -> 923
- mode1 -> 924
- mode2 -> 921
- mode3 -> 922

## R176 diagnostic
R176 is read-only and reuses the existing PlayAction trampoline.

At first D-pad route it queries:
- global entry function main+0x3F5560 for indexes 921..930;
- actor-local resolver main+0x768E84 for indexes 921..930, flag=1 and flag=0;
- remap main+0x769B04 for 921..924.

New markers:
- [NSC:R176] ACTION_REGISTRY
- [NSC:R176] ACTION_REGISTRY_SUMMARY

For global entries it logs:
- pointer/presence
- printable text at entry+0
- printable text at entry+7

Safety:
- registry insert = 0
- descriptor clone = 0
- action force = 0
- no new trampoline
- snapshots actor 0x1268/E94/E98/E9C and reports state_changed

## R176 decision tree
1. global922 == NULL
   -> asset/global registry load/export parity gap.
2. global922 != NULL but actor-local922 == NULL
   -> actor-local binding/availability parity gap.
3. global922 != NULL and actor-local922 != NULL but native still falls to921
   -> trace branch/remap decision one level deeper.

## Source verification
Expected:
NSC_RUNTIME_R176_SOURCE_VERIFY=PASS

R176 must not:
- revive R171,
- force action922 blindly,
- globally call SetAnmDirect930,
- globally suppress main+0x766320,
- modify P128,
- modify StageInfo,
- modify voice,
- add visibility hacks.


# R177 — ACTION DESCRIPTOR / BINDING PROVENANCE

## R176 hardware result (uzuy_log(18), Right D-pad)
- Right remains native mode3 and candidate922.
- Global entry922 is present and named `PL_ANM_SPTYPE_ACTION02` / `SPTYPE_ACTION02`.
- Actor-local lookup922 is NULL for both flag=1 and flag=0.
- Entries921 and 923..930 are globally present and actor-local present.
- Native remap is identity for 921..924, including 922->922.
- Probe state_changed=0.

Therefore the current root boundary is not input, candidate selection, native remap, or global CPK/global registry absence. The missing parity is actor-local action binding for index922.

## R177 target
Before any repair, prove whether actor action-record index922 itself contains a valid descriptor/resource key. Reuse the existing PlayAction hook at the hardware-proven fallback callsite and dump 921..930 through the P96-proven action-record table path.

R177 is strictly read-only:
- no binding-table write;
- no descriptor clone;
- no action force;
- no char281 gameplay branch;
- no additional trampoline;
- R172 UJ, P128, R164 StageInfo, voice freeze unchanged.

Decision after hardware test:
1. record922 descriptor/key valid + binding922 NULL -> repair actor binding construction from the native descriptor/resource path.
2. record922 descriptor NULL -> move one layer earlier into custom action-record population.
3. descriptor exists but key empty/unresolvable -> repair authored/resource-key parity, not D-pad selector.
