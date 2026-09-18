NSC2Switch P48A — UJ PATH PROBE (boot-safe)

Parent: P47A / R56
Fix vs first P48A: removed Membership 0x8800D0/0x880150 hooks.
Those are tiny tail-call stubs (relative B → 0x71C900); trampoline breaks them → no boot.

Hooks (log-only)
----------------
1. PlayAction @ 0x766B8C — ret + actor fields
2. Gate769A4C @ 0x769A4C — gate before 708 path @ 0x7E48EC
   FP: FC1D0FE8 A90157FE

READY
-----
play_action_ret=0x766b8c gate769=0x769a4c

Log
---
[NSC:P48A] PLAY_ACTION index=707/708/710 ret=1 f3668=281 ...
[NSC:P48A] GATE769A4C actor= ret= f3668= f4708= f536=

Hardware
--------
1. Boot — READY with gate769=0x769a4c
2. Vanilla UJ + Tobi UJ logs
3. Compare GATE769 near UJ window (Tobi expected when advancing 707→708)

ZERO gameplay delta.
Restore main:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
