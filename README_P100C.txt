NSC2Switch P100C — ONE-TRAMPOLINE ACTION710 ROUTE ORACLE
=========================================================
Why P100C exists
----------------
P100B failed before READY. Runtime log proved exlaunch aborted at hook_impl.cpp:602:
  Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)
The sixteen P100B inline installs consumed trampoline allocator capacity.
The later 0x696969... InvalidateNCE spam is fallout after that abort, not the root cause.

P100C design
------------
- Parent: P96A.
- Exactly ONE new trampoline: native helper main+0x64942C.
- Zero P100C inline hooks.
- Orig() called exactly once and return preserved.
- No E94/E9C/action/control writes.
- No forced 708/710.
- No char281 gameplay branch.

Why one helper is enough
------------------------
The proven action710 controller calls main+0x64942C from five route sites:
  LR 0x7E6AB4  PRE22
  LR 0x7E6ACC  PRE19
  LR 0x7E6AE4  PRE2A
  LR 0x7E6B20  ROUTE13   <-- decisive
  LR 0x7E6D68  NOT13_RECHECK22
At 0x7E6B24 native code compares the helper return with 0x13.
- ret == 0x13: continues to participant lookup/remap and the proven 710 path.
- ret != 0x13: branches away toward fallback handling.

Runtime test
------------
One session only:
1) vanilla UJ until cinematic succeeds;
2) Tobi custom UJ until the known failure;
3) save log and artifact.
Search for:
  [NSC:P100C] READY
  [NSC:P100C] ORACLE ... tag=ROUTE13 ... ret=... route13=...
Then run:
  python3 analyze_p100c_log.py uzuy_log.txt
