# NSC2Switch MASTER CHECKPOINT — 2026-09-29 R172

## Frozen baseline
- STORM CONNECTIONS Switch v1.70
- Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- original main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- original-main runtime architecture + resolver 7/7 + exact 30-word patch retained
- P128 retained
- R164 StageInfo CPK hardware PASS and frozen
- voice skipped/frozen by user
- D-pad paused

## R171 hardware verdict — RETIRED
R171 never matched. Its gate hook logged n=0..38 only while E94/E98=136/135. At frame74=3800/end78=4000 native gate still returned0. Immediately after, Event236 op23 `IXN0` executed; V2H `OP23_SAFE_SUPPRESS` performed SetActionImmediate(8), changing E94 136->8 while animation remained707. Once state left136, the 707 gate callback stopped, so R171's later 8/8 condition was unreachable inside that hook.

## Root compatibility gap
PC opcode23 contract is:
1. SetActionImmediate(param3)
2. resolve PL_ANM name
3. SetAnmDirect(resolved index)

Current V2H only does 1+2. On the UJ miss tail this gives state8 + animation707, exactly matching the looping symptom.

## Switch direct-animation proof
`main+0x766320` is promoted from rejected candidate to strong native SetAnmDirect equivalent based on corrected semantics:
- actor+0x1268 is animation state, so prior 928->930 hardware behavior is expected for PL_ANM930, not by itself evidence of a wrong function;
- `main+0x766A98` reads current animation from actor+0x218/+0x2C;
- native callers pass IDs 934/936/938/940/942 with defaults -1/0/rate1;
- `main+0x766A60` stores incoming W1 into actor+0x1268.

## R172 functional scope
On opcode23 only, after native SetActionImmediate and PL_ANM resolution, call 0x766320 only if:
- self target / side0
- custom semantic-UJ actor
- generated OugiAwakening member
- animation before and after pre-state request remains707
- requested state param3=8

Call ABI: `(actor, resolved_index, -1, 0, 1.0f)`.
No hardcoded char281 and no IXN0-string guard. No force708/710/74/77. All non-UJ opcode23 retains V2H suppression, keeping D-pad behavior unchanged.

## Hardware decision
PASS signature: `[NSC:R172] OP23_UJ_ANM_DIRECT ... pl_anm_index=150 anm1268=707->150 e94=136->8 ...` and visible loop stops without movement input.
If marker fires and 1268 becomes150 but visual still loops, the remaining issue is below the animation-index setter (render/clip object), not the action/state machine.
