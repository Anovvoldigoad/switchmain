P100A ACTION710 CORRIDOR LANDMARK TRACE — Switch v1.70

Purpose:
  Compare successful vanilla UJ vs custom UJ inside the proven native action710 producer corridor.
  P99A showed cleanup is downstream/fallback, not the cause of missing 710.

Functional parent: P96A. P97/P98/P99 installers are not called.
P100A adds five INLINE probes only; zero whole-function trampolines.
No BL/BLR replay. Replaced MOV/LDR instructions are reproduced exactly.
No state writes, no action rewrite, no forced 708/710, no char281 gameplay branch.

Markers:
  [NSC:P100A] READY
  [NSC:P100A] LANDMARK stage=ENTRY_7E6A58
  [NSC:P100A] LANDMARK stage=ZERO_PATH_7E6BB4
  [NSC:P100A] LANDMARK stage=C48RET_7E6B08
  [NSC:P100A] LANDMARK stage=LOOKUP_7E6C34
  [NSC:P100A] LANDMARK stage=REQUEST710_7E6EA8

Test in one session:
  1) successful vanilla UJ
  2) custom Tobi UJ through 707->708 failure
Then upload log and compiled artifact.
