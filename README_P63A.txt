NSC P63A — UJ ROUTER FIRST-DIVERGENCE TRACE (R72)

Purpose: roll back the disproven P60/P61/P62 gameplay deltas and trace the native
UJ decision chain read-only. P63A is based on the clean P59 behavior.

New hooks (read-only):
  0x7D3138  native vtable+0xF58 eligibility implementation
  0x7D2DE4  helper immediately after F58 in router
  0x7C6280  native control getter, logging only calls whose LR is inside C7600-C81A8

Retained P59 diagnostics:
  0x766320 central setter
  0x7B468C action-mode base
  existing P50 PlayAction broad player/custom log

P60 selector8 writes: REMOVED
P61 F58 false->true override: REMOVED
P62 persistent getter override: REMOVED
Gameplay writes added by P63: ZERO

Test:
  vanilla (Kakashi is fine): XA once, then XXA/UJ once
  Tobi: XA once, then XXA twice
  victim-UJ optional regression check
Then run: python3 analyze_p63a_log.py uzuy_log.txt
