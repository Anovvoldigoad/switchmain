NSC2Switch P47A — PLAY_ACTION RETURN-VALUE PROBE (log-only)

Parent: P46A / R55
Purpose: Why PlayAction(707) returns 0 on Tobi → diverts to 708, blocks 710-740 cinematic

Change vs P46A
--------------
PlayAction hook now:
  - Correct return type int32_t (callers CBNZ/CBZ on W0)
  - Logs ret= for every cinematic-range index
  - Dumps actor fields used inside PlayAction:
      +3668, +4708, +4712, +4740, +4756, +536

Log line:
  [NSC:P47A] PLAY_ACTION actor= index= ret= n= a2= f3668= f4708= f4712= f4740= f4756= f536=

Fingerprint unchanged @ 0x766B8C:
  A9BE57FE A9014FF4 B9529408 2A0403F4
  AA0003F3 7100091F 54000080 B9528668

ZERO gameplay delta.

Hardware test (REQUIRED)
------------------------
1. Boot — READY play_action_ret=0x766b8c
2. ONE vanilla UJ (cinematic OK) — full log
3. ONE Tobi Kamui UJ — full log
4. Diff for index=707:
     vanilla ret=?  fields=?
     Tobi    ret=0  fields=?
5. Same for 700,708,710,740

Decision
--------
- Tobi ret=0 and a field differs from vanilla → that field is the gate
- Tobi ret=0 and fields identical → fail deeper in 766CAC/768E2C/ANM bind
- Tobi ret≠0 but still no 710 → branch model wrong (re-check)

Restore main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
