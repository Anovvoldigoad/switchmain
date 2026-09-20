NSC2Switch P59A — ACTION-MODE DISPATCH PROVENANCE

PURPOSE
P58 proved both Tobi XXA attempts enter PlayAction with action445 from callsite 0x7B4B2C.
Static audit proves that callsite is inside the base action-mode implementation at 0x7B468C.
The virtual dispatch architecture is actor->vtable+0xE40; canonical thunk 0x7B4680 loads
that slot and BRs to the class implementation.

P59A answers the missing question WITHOUT changing gameplay:
WHO sends which mode into the base implementation, and which +0xE40 implementation does
the actor actually own when the wrong-jutsu route occurs?

WHAT CHANGED FROM P58A
- +1 read-only trampoline: ActionModeBase @ main+0x7B468C.
- Existing PlayAction logger now records ALL valid player-side (side0) calls, plus all custom
  actor calls. This removes the P58 vanilla-XA blind spot without adding a hook.
- P57 central setter retained as a cross-check.
- Event236 behavior is unchanged; op14 remains shadowed. P59 does NOT assume op14 is causal.

EXPECTED BOOT MARKER
[NSC:P59A] READY inherited_p50=1 central_setter=1 mode_base=1 added_over_p58=1 total_trampolines=7 writes=0 ...

DECISIVE MODE MARKER
[NSC:P59A] MODE_BASE ... char=... mode=... caller_off=0x... call_m4=... slot_off=0x... slot_word0=... base_impl=... action=A->B ...

DECISIVE PLAY MARKER
[NSC:P59A] PLAY_CALL ... char=... index=... caller_off=0x... callsite_off=0x...

HOW TO INTERPRET
- base_impl=1 / slot_off=0x7B468C:
  actor's virtual slot itself points to the base implementation. caller_off is the upstream
  invocation provenance (often caller of canonical thunk or an inline virtual call).
- base_impl=0 with slot_main=1:
  actor owns an override at slot_off. If MODE_BASE still appears, that override delegates to
  the base; audit the override before any patch.
- call_m4 recognized as BL/BLR by analyze_p59a_log.py:
  LR-4 is a genuine call instruction. If it is not a call, do NOT label caller_off-4 as the
  immediate base callsite; use slot_off + surrounding disassembly instead.

TEST PROTOCOL — KEEP IT CLEAN
A. Naruto control (side0)
   1. Fresh match, stand neutral.
   2. Press XA exactly once; let it fully finish.
   3. Return neutral.
   4. Press XXA once for UJ; let it fully finish.

B. Tobi custom (side0)
   1. Fresh match / enter the same True Awakening state used in P58.
   2. Wait until the moveset setup sequence is finished and Tobi is neutral.
   3. Press XA exactly once; let it fully finish.
   4. Return neutral.
   5. Press XXA exactly twice, waiting for each wrong XA/jutsu to fully finish before the next.
   6. Do not add unrelated attacks/support/awakening inputs during the capture.

C. Close emulator and send the FULL log plus the exact P59 artifact used.

WHY XA IS INCLUDED
The user's P58 run included Naruto XA after UJ, but P58 intentionally logged vanilla only when
index==700. P59 fixes that instrumentation blind spot, so Naruto XA and Tobi XA/XXA can be
compared at the same PlayAction and mode-dispatch layers.

DO NOT PATCH YET
P59 is the final provenance measurement at this layer. Do not rewrite 445, force 700, unshadow
Event236 op14, or hardcode char281 from this build.
