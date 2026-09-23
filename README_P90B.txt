NSC2Switch P90B — ZERO-EXTRA-TRAMPOLINE CINEMATIC HANDOFF TRACE

Parent: proven P89A phase-3 actor predicate bridge.
Reason for P90B: P90A failed boot because exlaunch trampoline allocation exhausted while installing new 0x768E84/0x769A4C trampolines.

P90B installs ZERO additional hooks. It reuses the already-installed P50 PlayAction trampoline and enriches its UJ-range record with EA4/BDA4/BDC8 before/after snapshots and caller offset.

Runtime markers:
  [NSC:P90B] READY ... zero_extra_trampolines=1
  [NSC:P90B] HANDOFF ... index=700..740 ... ea4=... bda4=... bdc8=...

No Event236/victim changes. No gameplay field writes. No forced action/F58/BDC8/EA4. No character 281 branch.

Test matrix: vanilla connected UJ through completed cinematic, then custom Kamui connected UJ until stuck. Send full uzuy log.
