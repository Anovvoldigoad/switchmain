NSC2Switch P119A — FINAL READ-ONLY UJ DAMAGE PROVENANCE
Target: STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Main Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
exlaunch: pinned 229bbd6

Purpose
=======
P118B corrected the ownership model: X19 / [actor+0xB9E4] at main+0x77B560 is the VICTIM being processed, not the UJ attacker. Successful control UJ fed victim DAMAGE_ID_SPATK_BEGIN_DIRECT (raw10), while Tobi fed DMG_MTOB_SPL01/raw15 then DMG_MTOB_SPL00/raw24.

P119A is the final read-only provenance run before a corrective patch. It reuses the already boot-safe P118B hook at main+0x3F4BC0 and correlates each victim damage record with the latest coherent side-0 UJ producer snapshot captured through existing P93 callbacks. No additional trampoline is added beyond the single P118B/P119 getter hook.

Markers
=======
[NSC:P119A] READY ... probe_ok=1
[NSC:P119A] LINK   n=... attacker UJ snapshot
[NSC:P119A] DAMAGE n=... victim damage code/index/raw/gate

LINK and DAMAGE with the same n are one provenance pair.

Safety
======
- read-only gameplay observation
- no event cursor write
- no damage index write
- no session creation
- no state/action forcing
- no force708 / force710
- no char281 gameplay branch
- P50 victim-safe Event236 compatibility preserved
- P89 generic UJ admission preserved

Test protocol
=============
1. Fresh boot after replacing the prior subsdk9 with the P119A artifact.
2. Confirm: [NSC:P119A] READY ... probe_ok=1
3. Perform ONE vanilla/control UJ that reaches its cinematic normally.
4. Perform ONE custom Tobi UJ until the known Kamui stuck/non-cinematic state appears.
5. Do not perform recovery attacks after the failure. Stop after a few seconds and save the full log.
6. Send the full log plus the GitHub Actions artifact.

Offline analyzer
================
python3 analyze_p119a_log.py uzuy_log.txt

Decision after this run
=======================
- If control has gate10=1 DAMAGE_ID_SPATK_BEGIN_DIRECT while Tobi paired damage never has gate10=1, the corrective patch moves upstream to the SPSKILL/damage-event selection producer. Do not patch B9E4, sessions, 137, or 710.
- If Tobi produces a gate10=1 record but the native cinematic still does not start, that would contradict P116-P118 and the exact row must be audited before patching.
- If the paired attacker context is stale (trace_gap > 16) or cursor != ptr_idx, treat the run as instrumentation-invalid, not gameplay proof.
