NSC2Switch P41A — CONTROL-BLOCK DUMP + OUGI CALLER TRACE

Parent: P40A (O14 actor-local direct + Event13/121/Ougi-core state trace)

P40A hardware result (uzuy_log(20)):
- Victim-UJ Naruto: PASS (Tobi does not disappear)
- StageMove: PASS
- EVT13_AWAKE count: 0  -> awakening never reaches native awake-condition event
- OUGI_CORE count: 0    -> Kamui never enters hooked ougi/UJ core
- CTRL14_DIRECT: many wrote=0 because old values are non-boolean (58, 26, 5, garbage)
  at candidate base actor+0x12A24  -> layout needs verification

P41A changes (diagnostic only, no new gameplay mutation):
1. Keep all P40A gameplay:
   - O14 actor-local direct at +0x12A24 (fail-closed boolean write)
   - O12 visibility shadow
   - O15 shadow
   - O2 StageMove live
   - O3/O4/O8/O13/O22/O23 live
   - vanilla charID <=280 native Event236
   - custom route generic 281..0xFFF
2. NEW: OugiCallerHook at main+0x488BAC (unique direct caller of 0x7E0F58)
   marker: [NSC:P41A] OUGI_CALLER ...
   If Kamui never hits OUGI_CALLER either, stuck handoff is upstream of UJ state entry.
3. NEW: CTRL_DUMP on first 4 custom O14 hits
   Dumps int32 window actor+0x12900 .. +0x12B00 (128 dwords)
   marker: [NSC:P41A] CTRL_DUMP n=... base+0x...: ...
   Purpose: locate true boolean control flags and correct base/relative map.

Expected READY:
[NSC:P41A] READY ... ctrl14_direct=1 control_base=0x12a24 ctrl_dump=1 ougi_caller=1 ...

Hardware test order (same as P40A):
1. Boot, verify READY + no fingerprint FAIL
2. Tobi vs Naruto slot1 -> enemy UJ once (victim must stay PASS)
3. Try awakening several times
4. Tobi Kamui UJ once; leave stuck state several seconds
5. StageMove once
6. Full fresh Uzuy log

Interpretation:
- OUGI_CALLER fires but OUGI_CORE does not -> unexpected (should not happen; caller BL's core)
- Neither OUGI_CALLER nor OUGI_CORE -> Kamui path never enters this UJ state machine
- CTRL_DUMP shows clean 0/1 clusters at a different base -> retarget O14 relative map next
- Still no EVT13_AWAKE -> continue upstream awakening eligibility work after layout is confirmed

Do NOT hardcode Tobi/281/COND_2DNZ.
Do NOT force awakening or alias condition names in this build.
Restore main SHA256 must remain 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9.
