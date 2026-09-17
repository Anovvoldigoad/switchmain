NSC2Switch P45A — COMBAT OUGI ACTION PROBE (log-only)

Parent: P44A (gameplay-identical)
Checkpoint: continue from MASTER CHECKPOINT r53 + P44A results

Purpose
-------
First battle-side probe of free-battle UJ action types.

RE facts (1.70 main):
  Combat action table ~0x1717E90 (entry size 0x30).
  Handlers are table-dispatched (0 direct BL callers).
  Dispatcher walker not yet bounded — handlers themselves are valid log points.

P45A adds TWO log-only hooks:

  text+0x6F44A0  NORMAL_OUGI
  Fingerprint:
    F81F0FFE F000D268 F9424508 2A0003E1
    F9762500 2A1F03E2 9400B71A 79401808

  text+0x6F4880  SPECIAL_OUGI_FINISH
  Fingerprint:
    F81F0FFE 7100001F 1A9F17E0 94062E11
    B40000A0 52800081 94037B8E 7100001F

Also retains P44A OugiFinishParam Create probe (init-only, expected 1 hit at boot).

NO gameplay policy change vs P44A / P43A:
  - O14 pure shadow (victim-UJ lock)
  - O12 visibility shadow
  - OP15 / OP17 / OP18 shadow
  - StageMove O2 live
  - OUGI_CORE / OUGI_CALLER logging-only (abandoned as fix)

READY expects:
  ougi_probe=1
  normal_ougi=0x6f44a0
  special_ougi_finish=0x6f4880
  vis12_shadow=1 ctrl14_shadow=1

Hardware test (REQUIRED order)
------------------------------
1. Boot — verify READY ougi_probe=1
2. ONE vanilla UJ with normal cinematic (e.g. Naruto)
3. ONE pure Tobi Kamui UJ (no StageMove in middle)
4. Full fresh Uzuy log

Decision matrix
---------------
- Vanilla: NORMAL_OUGI>=1 AND SPECIAL_OUGI_FINISH>=1  -> path healthy
- Tobi: NORMAL_OUGI>=1, SPECIAL_OUGI_FINISH=0         -> gap at finish transition
- Tobi: NORMAL_OUGI=0                                  -> gap earlier (entry)
- Vanilla both 0                                       -> wrong path; do not force

Restore main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

Forbidden until R55:
  - Gameplay writes
  - Hardcode 281
  - Restoring abandoned ougi-core live patch
  - op17/18 live "for Kamui"
