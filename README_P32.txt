NSC2Switch P32 — file-open vs XFBIN-read failure trace
======================================================

Purpose
-------
P31 confirmed that the custom parent manifest remains valid:
  data/spcload/mtobprm_load.bin.xfbin -> status 2.

The first preview children with proven native failures are:
  data/spc/mtobbod1acc.bin.xfbin -> 0 -> 5
  data/spc/mtobbod1_col3.xfbin   -> 0 -> 5

P31 also observed mtobbod1acc being retried later:
  5 -> 0 after a fresh LOAD_CREATE.

Native v1.70 disassembly now proves that status 5 is produced by two distinct
nuccLoadRequest branches:

  main+0x116F520
    status = 5 after main+0x1170FB0 returns 0.
    The native diagnostic text at that branch is:
      nuccLoadRequest.cpp, line 298
      "file could not be opened" (Japanese native string).

  main+0x116F5C0
    status = 5 after the XFBIN read path returns with the read-context error
    field at +0x1D8 equal to 1.

Therefore P32 does NOT modify resources. It only distinguishes those two
failure classes.

New read-only hooks
-------------------
  main+0x1170FB0 FILE_OPEN
    Logs path and native open result (1 success / 0 fail).

  main+0x116F404 PROCESS
    After native processing returns, logs:
      path
      load object's +0x68 status
      read context's +0x1D8 error field

All P31 hooks are retained:
  CPK_BIND, CHAR, LOAD_REQ, LOAD_CREATE, LOAD_STATUS transitions, CHUNK.

Interpretation
--------------
A) FILE_OPEN result=0
   -> search/provider/open failure for that exact child path despite parent
      manifest visibility. Investigate CPK path/index/binder semantics.

B) FILE_OPEN result=1, PROCESS status=5 readerr=1
   -> path opens, but XFBIN read/parse rejects the payload.
      Investigate PC-vs-Switch XFBIN/chunk binary compatibility.

C) FILE_OPEN result=1, PROCESS status=2
   -> child itself loads; move downstream to chunk/key/actor construction.

Build
-----
GitHub Actions workflow:
  Build NSC P32 file-open vs XFBIN-read trace

Expected artifact:
  NSC-P32-file-open-xfbin-read-trace-subsdk9

Deploy
------
Use the same clean P23A/R32 baseline used for P29/P30/P31.
Replace ONLY:
  atmosphere/contents/0100FA10190A0000/exefs/subsdk9

Expected READY:
  [NSC:P32] READY cpk=1 trace=1 ... process=0x116f404 open=0x1170fb0

Reproduce empty Tobi preview / failed VS, close Uzuy, then run:
  python3 analyze_p32_log.py /path/to/fresh_uzuy_log.txt

Send the full fresh log back to the project chat.
