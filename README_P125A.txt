P125A — P107-guided session-qualified state137 fallback (R141)

Goal:
Use the one thing P107 proved (state137 can drive native710/cinematic) without repeating P107 stale-context bugs.

Native-safe corridor:
- P124 gate raw->10 overlay remains narrow/generic.
- Native C48/type9/lookup/7EF098 calls are untouched.
- POST_OUTER is after native 7EF098 and records its real W0 return.

Functional fallback:
- Native cleanup instruction main+0x7EB27C is MOV W1,#125.
- It remains125 unless the SAME custom semantic-UJ actor has a successful native 7EF098 return AND context is mature: action708, E94=136,E98=135,E9C=0,BDA4=0,BDA8=0.
- Only then W1 becomes137. The native state-request BLR at0x7EB288 is untouched and performs validation/commit.

Never does:
- no char281 branch
- no direct 7EF098 call
- no force710
- no actor/event/session memory-field write
- no BL/BLR replay from subsdk9

Test order:
1) vanilla Naruto UJ (must not freeze)
2) Tobi as victim UJ (must remain safe)
3) Tobi own UJ once
4) save log before recovery actions
5) python3 analyze_p125a_log.py uzuy_log.txt
