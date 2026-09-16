NSC2Switch P40A — O14 PARITY + AWAKENING/KAMUI STATE TRACE

P40A is designed to collapse the remaining debugging rounds.
It inherits P39A's actor-local O14 parity candidate and adds read-only probes only.

Why this is grounded:
- P37A (O12 shadow) still failed victim-UJ.
- P38A added only O14 shadow and Naruto slot1, Isshiki, Naruto Sage and Kakashi victim-UJ all passed.
- The old O14 implementation main+0x751134(p3) ignored actor/p2 and does not match PC me_enable_control semantics.
- Event13 and Event121 callback addresses below are resolved from exact Switch v1.70 RELA entries, not guessed.

Runtime markers:
  [NSC:P40A] READY ... state_trace=1 ... ctrl14_direct=1 ...
  [NSC:P40A] CTRL14_DIRECT ...
  [NSC:P40A] EVT13_AWAKE ...
  [NSC:P40A] EVT121_COND ... text=...
  [NSC:P40A] OUGI_CORE ... mode=... ea0=... ea4=... ea8=...
  [NSC:P40A] EVT236 ...

Exact traced native boundaries:
  Event13  main+0x810614  (slot 0x2077A80)
  Event121 main+0x8134F8  (slot 0x20784A0)
  Ougi core main+0x7E0F58 (unique direct caller main+0x488BBC)

Recommended single-session hardware order:
1) Fresh boot, verify READY state_trace=1 and no fingerprint FAIL.
2) Tobi vs Naruto slot1: take enemy UJ once. Must remain normal if O14 direct parity is correct.
3) Try Tobi awakening several times from the normal state; do not trigger unrelated actions for a few seconds.
4) Use Tobi Kamui UJ once and let the stuck state remain for several seconds.
5) Trigger one fire jutsu/shuriken if that is the action that normally releases the victim; note when it happens.
6) Trigger StageMove once as regression control.
7) Close emulator and send the full fresh Uzuy log.

Interpretation is deterministic:
- no EVT13 during awakening attempt = upstream awakening eligibility/input gate;
- EVT13 but condition flow missing/failing = condition bridge target;
- EVT121 exposes exact names needed for generic data-driven aliasing;
- OUGI_CORE + all Event236 records around Kamui exposes the exact handoff/state transition.

P40A does not force awakening, does not alias condition names, and does not patch Ougi state.
Those fixes should be emitted only after this trace identifies the native boundary.
