NSC2Switch P44A — OUGI FINISH PARAM PROBE (log-only)

Parent: P43A (gameplay-identical)
Checkpoint: continue from MASTER CHECKPOINT r53

Purpose
-------
First evidence-gated probe of the OugiFinish / OugiFinishParam path on 1.70 main.

P43A proved:
  OUGI_CORE (0x7E0F58) and OUGI_CALLER (0x488BAC) are NEVER hit by free-battle UJ
  (vanilla Naruto or Tobi Kamui). Path abandoned.

P44A adds ONE new solid hook:
  text+0x4726E4  — OugiFinishParam Create / load path
  Fingerprint (8 words):
    D102C3FF A9057BFD A9066FFC A90767FA
    A9085FF8 A90957F6 A90A4FF4 F000AFB3
  This is the manager Create (init-time). Unique caller is the big manager-init
  sequence at 0x40631C. Logging confirms the manager path is live; it is NOT
  expected to fire per-UJ. Next RE iteration will target Ougi::Update /
  ougiFinish index assignment after this baseline.

NO gameplay policy change vs P43A / P42A:
  - O14 pure shadow (victim-UJ lock)
  - O12 visibility shadow
  - OP15 / OP17 / OP18 shadow
  - StageMove O2 live
  - All previous resource / Event236 / CPK paths unchanged
  - OUGI_CORE / OUGI_CALLER remain logging-only (already abandoned as fix)

READY expects:
  ougi_finish=1
  ougi_finish_create=0x4726e4
  vis12_shadow=1 ctrl14_shadow=1 ougi_log_all=1 evt13_log_all=1

Hardware test (REQUIRED order)
------------------------------
1. Boot — verify READY line contains ougi_finish=1
2. ONE vanilla UJ with normal cinematic (e.g. Naruto)
3. ONE pure Tobi Kamui UJ (no StageMove in middle)
4. Full fresh Uzuy log

Decision matrix
---------------
- OUGI_FINISH_CREATE appears at boot (n=0 or small)          → manager path live (expected)
- Still 0 OUGI_CORE for both chars                           → confirms abandon (already locked)
- Any new marker difference vanilla vs Tobi                  → record for R54
- If Create never fires                                      → fingerprint or main mismatch; stop

Restore main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

Forbidden until R54:
  - Gameplay writes
  - Hardcode 281
  - Restoring any abandoned ougi-core live patch
  - op17/18 live “for Kamui”
