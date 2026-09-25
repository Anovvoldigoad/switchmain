NSC P111A — Victim / Participant State Provenance (READ ONLY)
R122 / 2026-09-25

Purpose
=======
P110 proved that the failing custom Tobi own-UJ never invokes the native type10
cinematic manager. In the successful same-session vanilla control, the victim is
already state126 and receives PlayAction12 from main+0x7DE9B0 before the manager
appears. In the failing Tobi route the victim instead traverses state39/state121.
Therefore P111 moves one diagnostic trampoline to the native state-request
gateway main+0x7A89A4 and records the victim/participant states that distinguish
those paths.

P111 logs only requested states:
  39, 81, 121, 125, 126, 137

It is READ ONLY:
- requested state unchanged
- arg2/arg3 unchanged
- native Orig called exactly once on each runtime path
- no 125->136 or 125->137 mapping
- no force708 / force710
- no char281 gameplay branch
- P50 victim-safe VIS/O14 shadow remains inherited

Static landmarks verified
=========================
main+0x7A89A4  native state-request gateway (hooked)
main+0x7A8A9C  simple/direct E9C setter family (fingerprinted only)
main+0x7DE9AC  BL PlayAction12
main+0x7DE9B0  return after native victim PlayAction12
main+0x74F954  type10 cinematic manager (fingerprinted only; P110 hook retired)
main+0x74FF7C  return after native manager request137

Runtime test
============
1) one vanilla UJ that reaches cinematic
2) one Tobi own-UJ that fails naturally
Do not use P107/P108 mapping builds for this test.

Expected diagnostic split
=========================
Vanilla victim: identify exact caller(s) for state125/state126, then PlayAction12.
Tobi victim: identify exact caller(s) for state39/state121.

If inherited P93 shows committed E94=126 but P111 has no req126 for that actor,
state126 bypasses main+0x7A89A4; treat main+0x7A8A9C/simple-setter family as the
next provenance target instead of guessing another state remap.

Analyzer
========
python3 analyze_p111a_log.py uzuy_log.txt
