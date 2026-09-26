P127A — full native corridor A/B with robust latch observability (R143)

Purpose
- P126 artifact was correctly deployed, but custom Tobi still produced GATE bridge=1 followed by no visible AFTER_ACTOR/AFTER_PEER/TYPE9/POST_OUTER markers and later CLEANUP session=0/mature=0.
- P126's paired main really did contain the actor reject NOP at main+0x77C494, so absence of the filtered marker is not proof that the static patch was missing.
- P124 downstream focus re-queried transient semantic/opposite-side state after native helpers. P127 trusts only the actor latch that was already armed by the strict custom+semantic+action707+opposite-side+appended-damage gate.

Causal A/B main patches
- 0x77C494 actor C48 reject: NOP
- 0x77C4A8 peer C48 reject: NOP
- 0x77C4B4 type9 branch: unconditional B 0x77C514
- 0x77C520 lookup branch: unconditional B 0x77C59C

All native calls remain intact and execute from main exactly once:
- actor C48 BLR 0x77C490
- peer C48 BLR 0x77C4A4
- type9 query BL 0x77C4B0
- lookup BL 0x77C51C
- outer setup BL 0x77C5E8 -> 0x7EF098

P125 session-qualified P107 endpoint remains enabled. It can only map cleanup125->137 after native 0x7EF098 returns success for the same latched custom actor AND the actor context is mature (E94=136,E98=135,E9C=0,BDA4=0,BDA8=0). It does not force710.

This build is a causal A/B, not final policy if it succeeds, because four branch outcomes are statically opened for any corridor entry that reaches them. Successful vanilla UJs normally already take these success outcomes, but regression testing is mandatory.

Test order
1) Naruto own UJ once.
2) Tobi as victim of UJ once.
3) Tobi own UJ once; save log immediately without recovery jutsu.

Expected useful markers
[NSC:P127A] READY
[NSC:P124A] GATE
[NSC:P124A] AFTER_ACTOR
[NSC:P124A] AFTER_PEER
[NSC:P124A] TYPE9_ZERO
[NSC:P125A] POST_OUTER
[NSC:P125A] CLEANUP

Interpretation
- POST_OUTER ret=1/session_latch=1: native cinematic-session outer setup finally succeeded.
- CLEANUP bridge=1 after that: P107 endpoint is being reused only with qualified setup.
- If POST_OUTER appears but ret=0: root is inside 0x7EF098/session registration.
- If even with forced success branches POST_OUTER never appears: there is another control-flow exit between 0x77C59C and 0x77C5E8, and that exact block is next.
