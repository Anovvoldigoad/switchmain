NSC2Switch P46A — PLAY_ACTION PROBE (log-only)

Parent: P45A (gameplay-identical)
Checkpoint: MASTER CHECKPOINT r54

Purpose
-------
Mid-battle UJ cinematic path probe.

RE (r54 + follow-up):
  PL_ACT_SPSKILL_DEMO_ATK  = UJ cinematic demo state (table ~0x172C2A8)
  PlayAction @ text+0x766B8C plays PL_ACT_* by index
  Already used by HandleActionAnimation (Event236)
  NORMAL_OUGI / SPECIAL_OUGI_FINISH = end classifiers (both fire Tobi+vanilla) — NOT the gap

P46A adds log-only hook:

  text+0x766B8C  PlayAction
  Fingerprint:
    A9BE57FE A9014FF4 B9529408 2A0403F4
    AA0003F3 7100091F 54000080 B9528668
  Log: PLAY_ACTION actor= index= n= a2= rate=

Retains P45A probes (Create, NORMAL_OUGI, SPECIAL_OUGI_FINISH).

NO gameplay policy change vs P45A:
  O14 pure shadow, O12/15/17/18 shadow, StageMove live, ougi-core abandoned

READY expects:
  ougi_probe=1 play_action=0x766b8c

Hardware test (REQUIRED)
------------------------
1. Boot — READY ougi_probe=1 play_action=0x766b8c
2. ONE vanilla UJ with normal cinematic (e.g. Naruto) — full log
3. ONE pure Tobi Kamui UJ — full log
4. Diff PLAY_ACTION index sets in UJ window (±3s around UJ)

Decision matrix
---------------
- Vanilla has index set V during UJ; Tobi missing subset of V
  -> those indices are cinematic path; next RE maps index -> PL_ACT name
- Both have identical PLAY_ACTION indices during UJ
  -> gap downstream of PlayAction (demo asset bind / camera)
- Tobi has ZERO PLAY_ACTION during UJ attempt
  -> never enters play path; gap is state transition TO SPSKILL_DEMO_ATK

Restore main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

Forbidden until R55+:
  - Gameplay writes
  - Hardcode 281
  - Restoring abandoned live patches
