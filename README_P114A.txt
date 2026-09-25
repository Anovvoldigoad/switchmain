NSC2Switch P114A — exact type9 preflight provenance (READ ONLY)
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70

Why P114A exists
----------------
P113A proved a successful vanilla UJ calls main+0x7EF098 and creates a type10
cinematic session, while failing custom Tobi never calls 0x7EF098 at all.
The exact successful vanilla caller is return main+0x77C5EC (BL at 0x77C5E8).

Static back-slice before 0x77C5E8:
  event field +0x50 must be type 10/11
  actor vslot +0xC48 must pass
  peer  vslot +0xC48 must pass
  0x77C4B0 -> 0x750860(type9)
  if ret==0, native continues via 0x795ED0 -> 0x7F78FC and pairing setup
  then 0x77C5E8 -> 0x7EF098

P114A places exactly one read-only trampoline on main+0x750860.  It logs ONLY
when caller return == 0x77C4B4 and type==9.  All other query calls immediately
pass through to native behavior.

Interpretation
--------------
Vanilla should produce:
  [NSC:P114A] PREFLIGHT ... type=9 ret=0 caller_off=0x77c4b4

Custom Tobi:
  no PREFLIGHT -> never reaches the event/type10-11 + C48 preflight path;
                  root is earlier than 0x77C4B0.
  PREFLIGHT ret=1 -> existing type9 session is the blocker.
  PREFLIGHT ret=0 but still no 710 -> type9 passed; next frontier is the
                                      0x795ED0 -> 0x7F78FC / pairing corridor.

Test discipline
---------------
1. One successful vanilla UJ.
2. One Tobi own-UJ until absorb/stuck/fallback.
3. Do not use recovery shuriken/jutsu before saving the log.
4. Run: python3 analyze_p114a_log.py uzuy_log.txt
