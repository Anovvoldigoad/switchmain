# NSC2Switch Runtime R172 — UJ Miss SetAnmDirect Parity

R172 retires the R171 flag70 mutation. Hardware R171 proved the real whiff desync occurs when Event236 opcode23 requests state 8 and resolves PL_ANM `IXN0` to index 150, while V2H intentionally suppresses the second PC operation (`SetAnmDirect`). The result is logical state 136->8 with animation 707 left running.

R172 preserves `SetActionImmediate(param3)` and restores the missing direct-animation operation only for the proven custom semantic-UJ miss context: self target, OugiAwakening member, animation 707, requested state 8. It calls Switch `main+0x766320(index,-1,0,1.0f)`. This target now has static native proof as an animation setter: companion `0x766A98` reads current animation; native callsites feed animation indexes; the function stores incoming W1 to actor+0x1268.

All other opcode23 calls remain on V2H fail-closed suppression, so D-pad behavior is unchanged. No action708/710/74/77 is forced. Stage R164, P128, voice, and D-pad logic are otherwise unchanged.

Expected miss marker:
`[NSC:R172] OP23_UJ_ANM_DIRECT ... pl_anm_index=150 anm1268=707->150 e94=136->8 ...`
