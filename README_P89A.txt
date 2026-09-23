NSC2Switch P89A COMPLETE — GENERIC PHASE-3 ACTOR-PREDICATE BRIDGE
Required baseline: d7181c6 (P88B BOOT PASS).

EXTRACT CONTENTS OF THIS ZIP DIRECTLY INTO REPO ROOT.
There is intentionally NO P89KIT wrapper folder.

1. Confirm:
   git log --oneline -1
   d7181c6 Fix P88B CI exlaunch bootstrap

2. Run:
   python3 APPLY_P89A_COMPLETE.py
   python3 verify_p89a_source.py

3. Must end:
   P89A_SOURCE_SANITY=PASS

4. Push:
   git add -A
   git commit -m "P89A generic phase3 actor predicate bridge"
   git push origin main

Use ONLY workflow:
  Build NSC P89A generic phase3 actor predicate bridge

Expected artifact:
  NSC-P89A-phase3-actor-predicate-bridge

DO NOT TEST an artifact named P88B.

Boot log MUST contain:
  [NSC:P89A] READY ... probe=1

P89A policy:
- native TRUE always preserved
- native FALSE bridged only at BDA4=3 / BDC8=1
- semantic UJ must be enabled
- generated OugiAwakening membership required
- no char281 hardcode
- no BDA4/BDC8/F58/action writes
- no 445->700 rewrite
- no selector8

Also corrects P88B snapshot labels/offsets:
  116F4 -> 106F4
  133E0 -> 123E0
  133E4 -> 123E4

Test:
vanilla XA x2; vanilla UJ x2; custom XA x2; custom intended UJ x2; then awakened custom UJ if transition succeeds.
Analyze with:
  python3 analyze_p89a_log.py uzuy_log.txt
