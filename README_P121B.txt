NSC P121B — boot-safe static peer C48 branch bypass A/B

Why this build exists
---------------------
P121A did not reach game boot. Runtime log proved exlaunch aborted while installing
its second corrective inline hook:
  hook_impl.cpp:602
  Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)X
P120A had already reached READY immediately before the abort.

P121B architecture
------------------
- Keeps P120A as the ONLY new runtime inline hook.
- Adds ZERO P121 hooks/trampolines.
- Paired v1.70 main has exactly one instruction changed:
    main+0x77C4A8: CBZ W0,0x77C5EC (0x34000A20)
                  -> NOP            (0xD503201F)
- The native peer C48 call at main+0x77C4A4 remains intact and executes normally.
- No direct 0x7EF098 call, no session creation, no force708/710, no char281 branch.

Important
---------
This is a functional causal A/B, NOT the final generic policy. The branch bypass
also applies to vanilla type10/11 corridor entries that reach this point. Normal
successful vanilla UJs already have peer C48=true, so their successful path should
be unchanged, but edge-case peer rejection semantics are intentionally bypassed.

Test
----
1. Fresh boot and confirm:
   [NSC:P120A] READY ... patch_ok=1
   [NSC:P121B] READY ... patch_ok=1
2. One vanilla control UJ.
3. One Tobi custom UJ until the known capture point.
4. Stop after a few seconds; do not recover with jutsu/shuriken.
5. Send the full fresh log + Actions artifact.

Interpretation
--------------
- If Tobi now reaches cinematic / 0x7EF098 lifecycle / native710:
  peer C48 rejection is causally confirmed. Final repair moves upstream to the
  missing readiness semantics; do not keep this global branch bypass as final.
- If still stuck and no lifecycle:
  actor/victim C48 at 0x77C490 or the type9/downstream corridor is next.
