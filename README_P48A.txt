NSC2Switch P48A — UJ PATH PROBE (708 vs 710)

Parent: P47A / R56
Goal: Why Tobi advances 707→708 while vanilla reaches 710

Hooks (log-only)
----------------
1. PlayAction @ 0x766B8C — ret + actor fields (kept from P47A)
2. Membership @ 0x8800D0 — list check before 710 path
3. Membership @ 0x880150 — variant
4. Gate @ 0x769A4C — gate immediately before 708 path @ 0x7E48EC

READY
-----
play_action_ret=0x766b8c member=0x8800d0 gate769=0x769a4c

Log lines
---------
[NSC:P48A] PLAY_ACTION ... index= ret= ...
[NSC:P48A] MEMBER8800D0 x0= ret= n=
[NSC:P48A] MEMBER880150 x0= x1= ret= n=
[NSC:P48A] GATE769A4C actor= ret= n= f3668= f4708= f536=

Hardware test
-------------
1. Boot — all three OK fingerprints
2. Vanilla UJ (cinematic) — full log
3. Tobi Kamui UJ — full log
4. Compare around 700-740:
   - GATE769A4C ret (Tobi should fire near 708)
   - MEMBER8800D0/150 ret (vanilla should pass near 710; Tobi?)

Decision
--------
- Tobi GATE769 ret!=0 + 708, vanilla no GATE near UJ → 708 path is Tobi branch
- Vanilla MEMBER ret!=0 near 710, Tobi MEMBER ret=0 → membership is the gate
- Both MEMBER pass but Tobi no 710 → state-machine enum elsewhere

ZERO gameplay delta.
Restore main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
