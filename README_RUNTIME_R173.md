# NSC2Switch Runtime R173 — UJ Miss SetAnmDirect Parity

R173 retires the R171 flag70 mutation. Hardware R171 proved the real whiff desync occurs when Event236 opcode23 requests state 8 and resolves PL_ANM `IXN0` to index 150, while V2H intentionally suppresses the second PC operation (`SetAnmDirect`). The result is logical state 136->8 with animation 707 left running.

R173 preserves `SetActionImmediate(param3)` and restores the missing direct-animation operation only for the proven custom semantic-UJ miss context: self target, OugiAwakening member, animation 707, requested state 8. It calls Switch `main+0x766320(index,-1,0,1.0f)`. This target now has static native proof as an animation setter: companion `0x766A98` reads current animation; native callsites feed animation indexes; the function stores incoming W1 to actor+0x1268.

All other opcode23 calls remain on V2H fail-closed suppression, so D-pad behavior is unchanged. No action708/710/74/77 is forced. Stage R164, P128, voice, and D-pad logic are otherwise unchanged.

Expected miss marker:
`[NSC:R173] OP23_UJ_ANM_DIRECT ... pl_anm_index=150 anm1268=707->150 e94=136->8 ...`


## R173 delta — read-only D-pad route trace

Parent is the exact R172 full-source package from Google Drive, not a V2H reconstruction.
R173 reuses the already-installed PlayAction trampoline and adds **zero new hooks/trampolines**.

It logs only custom-player PlayAction calls at the two hardware-proven route callsites:
- `main+0x646CFC` requesting animation/action `921`
- `main+0x647080` requesting animation/action `928`

Markers:
- `[NSC:R173] DPAD_ROUTE_PRE ...`
- `[NSC:R173] DPAD_ROUTE_POST ...`

Snapshot fields are read-only:
`actor+0x12B78/+0x12B7C/+0x12B80/+0x12B84/+0x12B88`, `F30`, `E94/E98/E9C`, `BDA4/BDA8/BDC8`, and `0x1268`.

Safety invariants:
- R172 UJ-miss SetAnmDirect parity retained exactly.
- non-UJ opcode23 remains V2H-safe-suppressed.
- P128 retained.
- V2N/V2P stage probes retained.
- no char281 gameplay branch.
- no D-pad state write.
- no visibility/damage force.
