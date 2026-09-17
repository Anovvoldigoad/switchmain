NSC2Switch P43A — OUGI/EVENT13 UNFILTERED LOGGING (gameplay-identical to P42A)

Purpose: fix methodology error in P42A logs.
P42A only logged OUGI_CORE / OUGI_CALLER / EVT13 when char_id > 280.
Vanilla UJ control logs could never show those markers even if the functions ran.

P43A change (LOGGING ONLY):
- OUGI_CORE, OUGI_CALLER, EVT13_AWAKE log for ALL characters (vanilla + custom)
- Cap 1024 entries each
- NO gameplay policy change vs P42A:
  O14 pure shadow, O12 shadow, OP15/17/18 shadow, StageMove live, etc.

READY expects: ougi_log_all=1 evt13_log_all=1

Hardware test (REQUIRED order):
1. Boot — verify READY
2. ONE vanilla UJ with normal cinematic (e.g. Naruto) — note if cinematic OK
3. ONE pure Tobi Kamui UJ (no StageMove in middle) — note capture + missing cinematic
4. Full fresh Uzuy log

Decision matrix from log:
- Vanilla has OUGI_CORE, Tobi does not  -> custom ID UJ entry gap
- Neither has OUGI_CORE               -> 0x7E0F58 is NOT general UJ entry; abandon that path
- Both have OUGI_CORE                 -> inspect mode/state args for differences

Restore main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
