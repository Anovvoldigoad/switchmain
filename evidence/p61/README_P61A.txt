NSC P61A — UJ ELIGIBILITY GATE COMPAT
=====================================
Purpose
-------
P60 hardware proved the MovesetPlus UJ-enable event can set Switch native control
selector8, but Tobi still never reached PlayAction700. Static v1.70 reconstruction
shows selector8 is downstream: the router first calls actor vtable+0xF58 at
main+0xC7870. Both Kakashi and Tobi use main+0x7D3138 for this slot.

P61 therefore ports compatibility at that exact eligibility boundary. It preserves
native TRUE and only converts native FALSE->TRUE for a generic custom actor that:
- explicitly received Event236 op14 p2=0 p3=1 (source UJ enable),
- is called with F58 mode/w1=0,
- is entered from exact router return LR main+0xC7874,
- and can refresh native selector8 successfully.

No action/state is forced. Native code after the gate still selects 0x87 and invokes
its normal state request path.

Expected runtime markers
------------------------
[NSC:P61A] READY ... uj_f58_gate=1 ...
[NSC:P61A] UJ_GATE_COMPAT ... orig=0 override=1 caller_off=0xc7874 ...
[NSC:P59A] PLAY_CALL ... char=281 index=700 ...   <-- success criterion

Test sequence
-------------
1) Kakashi XA once -> neutral -> UJ once -> finish.
2) Tobi setup/True Awakening as usual.
3) Tobi XA once -> finish.
4) Tobi XXA once -> finish.
5) Tobi XXA once again -> finish.
6) Victim regression: let vanilla opponent UJ hit Tobi once; after cinematic verify
   Tobi remains visible and playable.
7) Close emulator and keep full log.

Run analyzer:
  python3 analyze_p61a_log.py uzuy_log.txt

PASS requires a guarded P61 gate override followed by custom PlayAction700.
A P61 gate override with no custom 700 is NOT success.
