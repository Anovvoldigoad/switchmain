NSC2Switch P31 — child status-transition trace
===============================================

Purpose
-------
P30 proved that the parent data/spcload/mtobprm_load.bin.xfbin reaches native
status 2, but its 512 LOAD_STATUS log budget was exhausted by repeated polling
of two child failures before the rest of the mtob children could be classified.

P30 fresh-run facts carried into P31:
- ID281 resolves to mtob.
- external Tobi_Switch.cpk bind succeeds.
- mtobprm_load.bin.xfbin: LOAD_CREATE + LOAD_REQ + status 2.
- data/spc/mtobbod1acc.bin.xfbin: status 0 -> 5 (first child failure).
- data/spc/mtobbod1_col3.xfbin: status 0 -> 5 shortly after.
- mtobskl3 was not requested in the P30 runtime trace.
- no custom CHUNK event was reached before those file-load failures.

What P31 changes
----------------
P31 is still read-only. It does NOT alias IDs, replace paths, inject resources,
or modify game state. The only diagnostic change is LOAD_STATUS logging:

- first observed status for each custom path is logged once;
- later logs are emitted only when that path's status changes;
- a fixed 128-entry table tracks paths, with a 1024 transition-log ceiling.

This prevents mtobbod1acc / mtobbod1_col3 polling from hiding the final states
of the later prm_load children. CHAR, CPK_BIND, LOAD_REQ, LOAD_CREATE and CHUNK
traces are otherwise preserved from P30.

Build
-----
Run GitHub Actions workflow:
  Build NSC P31 child status transition trace

Expected artifact:
  NSC-P31-child-status-transition-trace-subsdk9

Deploy
------
Start from the exact clean P23A/R32 baseline that produced the valid P29/P30
mtob traces. Replace ONLY:
  atmosphere/contents/0100FA10190A0000/exefs/subsdk9

Do not add P27/P28 aliases or experimental loose resources.

Expected marker:
  [NSC:P31] READY cpk=1 trace=1 ...

Key output format:
  [NSC:P31] LOAD_STATUS ... path=<path> first=1 prev=4294967295 status=0
  [NSC:P31] LOAD_STATUS ... path=<path> first=0 prev=0 status=2

For a failing child the transition should look like 0 -> 5.

After reproducing the empty Tobi preview / VS failure, close Uzuy and run:
  python3 analyze_p31_log.py /path/to/fresh_uzuy_log.txt

Then send the full fresh log back to the project chat.
