NSC2Switch P90A — BOOT-SAFE CINEMATIC HANDOFF TRACE
====================================================
Target: Storm Connections Switch v1.70 / 0100FA10190A0000

Purpose
-------
P89A already solves generic UJ admission: custom semantic/member actor reaches
BDC8=2, F58=true, native action700, then 707/708. P90A is READ-ONLY tracing for
the remaining cinematic/hit-confirm handoff failure.

New P90A probes
---------------
- main+0x768E84 ActionLookup(actor,index,flag), focused on UJ 700..740.
- main+0x769A4C ActionGate(actor), logged only in the UJ corridor / proven caller.
- inherited main+0x766B8C PlayAction trace is reused; it is NOT double-hooked.
- snapshots: E60/E94/E98/E9C/EA0/EA4/BDA4/BDC8 + caller offset.

Safety
------
P89 bridge remains unchanged. No Event236/victim change. No state/action write,
no EA4 write, no F58 override, no force700/708, no selector8, no char281 branch,
no virtual BLR replay, no hook on the large 0x7E47B8 dispatcher.

Test matrix
-----------
1) Vanilla UJ that connects and completes cinematic.
2) Custom UJ/Kamui that connects and becomes stuck.
Prefer same opponent/conditions. Upload the complete emulator log.

Expected markers
----------------
[NSC:P90A] READY
[NSC:P90A] LOOKUP
[NSC:P90A] GATE
plus inherited [NSC:P89A], [NSC:P59A] PLAY_CALL, [NSC:P55A] ACTION_ROUTE.
