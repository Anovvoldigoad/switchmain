NSC2Switch P109A — state137 provenance probe (R120)

Purpose
=======
P108A is RETIRED by runtime evidence. Its exact 125 -> 136 bridge fires, but
committing state136 after custom action708 re-enters controller +0x518 at the
mode0 entry and immediately calls PlayAction707 at main+0x7E4858/return
0x7E485C. Runtime therefore goes backwards 708 -> 707 and reproduces the
Kamui replay/stuck/uncontrollable behavior.

The same P108 session contains a successful vanilla UJ control. Native char276
stays action707/state136 while handoff state matures:
  E9C=0,   BDA4=0, BDA8=1, EA4=0x708
  E9C=137, BDA4=0, BDA8=0, EA4=0x76C
Then state137 commits and +0x520 produces PlayAction710 at return 0x7E6EC8.

P109A does NOT try another functional bridge. It identifies the native writer
of state137 first.

Probe
=====
One read-only whole-function trampoline at main+0x7A89A4, the proven base
request-state gateway. Only requested states 125, 136, 137 are logged.

Every focused call logs:
- actor / side / char ID
- requested state and arg2/arg3
- caller return offset
- action pre/post
- E94/E98/E9C pre/post
- EA4/EA8 pre/post
- BDA4/BDA8/BDC8 pre/post
- dynamic vtable +0xE28 target
- native return

Safety
======
- Orig called with unchanged requested_state/arg2/arg3
- no state mapping
- no direct state/control write
- no force708 / no force710
- no char281 gameplay branch
- P50 victim-safe Event236 shadows preserved
- P89 generic UJ admission preserved
- functional P108/P107 hooks absent
- exactly one new trampoline

Decision
========
Run one successful vanilla UJ first, then one failing Tobi UJ.

A) P109 logs vanilla `req=137`:
   caller_off is the exact native producer. Next patch/probe goes to that
   producer and compares its native condition against custom action708.

B) P93/P81 shows vanilla E9C 0->137 but P109 logs NO vanilla `req=137`:
   state137 bypasses main+0x7A89A4. Next target is the independently
   fingerprinted direct/simple E9C writer family main+0x7A8A9C.

C) Custom naturally logs req137:
   compare caller/args/raw state against vanilla before changing anything.

Do not judge P109 by audio, visibility, or stage parity. Those Event236 gaps are
independent and remain intentionally untouched until the 708->710 handoff is
localized correctly.
