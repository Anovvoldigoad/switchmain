NSC2Switch P44A — OUGI FINISH INDEX LOG-ONLY PROBE

Purpose:
  Log-only probe at the function that actively uses the debug format
  "ougiFinish index[%d:%d] side[%d] role[%d]".

Target:
  main + 0x44F264
  Fingerprint: D10203FF F9001BFE A90467FA A9055FF8 A90657F6 A9074FF4 AA0003F3 AA0103E0

Change vs P43A:
  - NEW: trampoline log at 0x44F264 (all characters, cap 1024)
  - Gameplay policy identical to P43A (O14 pure shadow, O12 shadow, etc.)
  - Zero gameplay writes

READY expects: ougi_finish_index=1

Hardware test (REQUIRED order):
1. Boot — verify READY + fingerprint OK
2. ONE vanilla UJ with normal cinematic (e.g. Naruto)
3. ONE pure Tobi Kamui UJ
4. Full fresh Uzuy log

Decision matrix:
- Vanilla has hits, Tobi does not  -> entry gap for custom ID
- Both have hits                  -> compare args / mode / side
- Neither has hits                -> this is also not the free-battle UJ gate

Restore main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
