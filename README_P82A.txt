NSC2Switch P82A — Downstream UJ Corridor Trace
===============================================

Target:
Naruto x Boruto Ultimate Ninja STORM CONNECTIONS
Nintendo Switch update 1.70

Purpose
-------

P81A successfully clears the data-driven OugiAwakening veto at the
exact +0x1288 Ultimate-Jutsu decision.

Runtime then proves 0x8B2B70 may return 1 while the actor still requests
and plays action445.

Therefore 0x8B2B70 is not final UJ acceptance.

P82A traces the downstream native UJ corridor.

Targets
-------

0x794EC8
caller return 0x7F4660

0x64A030
caller return 0x7F4680

0x7C5FFC
caller return 0x7F4698

0x7D2DE4
caller returns 0x7F46C8 and 0x7F4780

0x7C6280
caller returns:
0x7F4790
0x7F47E4
0x7F4814

Safety
------

P82A:
- keeps P81A active
- is read-only
- preserves all Orig() return values
- does not hook inline F58
- does not force state87
- does not force action700
- does not rewrite action445
- contains no char281 gameplay branch

Runtime goal
------------

One failing XXA attempt should reveal the exact post-P77 branch sequence
that still reaches action445.
