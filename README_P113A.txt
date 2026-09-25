P113A — cinematic type10 session setup provenance (read-only)

Why this probe exists
---------------------
P110 proved successful vanilla Ultimate Jutsu owns/runs the type10 cinematic manager, while failing custom Tobi never enters that manager. P112B then disproved the assumption that victim state125->126->action12 is a universal prerequisite: a successful vanilla UJ against a different victim reached 710 without any 0x7EB270 invocation. The universal frontier is therefore type10 session creation itself.

Static v1.70 chain
------------------
0x7EF098 outer setup wrapper
  -> 0x7EF128 inner setup
     -> query type9 @ 0x750860
     -> query type6 @ 0x750860
     -> resolve peer @ 0x796384
     -> peer +0xCB8 virtual context
     -> 0x7EF1B0 BL 0x7514AC
        -> MOV W1,#10
        -> 0x750C78 record insert/config

P113A moves the one diagnostic trampoline to 0x7EF098. It captures caller LR first, snapshots actor/peer, queries active session types 6/9/10 before and after the native function, calls Orig(actor) exactly once, and preserves the native return.

No state mapping, no manual session creation, no forced action708/710, no char281 branch.

Test
----
1. One successful vanilla UJ.
2. One Tobi own-UJ until the opponent is absorbed/stuck.
3. Do not recover the opponent before saving the log.

Expected marker:
  [NSC:P113A] READY ... probe_ok=1
  [NSC:P113A] SESSION ...
  [NSC:P113A] PEER ...

Analyze:
  python3 analyze_p113a_log.py uzuy_log.txt
