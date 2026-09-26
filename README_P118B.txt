P118B — EXACT EVENT CURSOR / TABLE IDENTITY CENSUS (READ ONLY)
================================================================
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70

Why P118B exists
----------------
P118A current runtime proved:
- successful control action707 selected raw11/norm10 at global idx=124 and reached 710;
- custom char281 action707 selected idx=1848 raw15, then idx=1847 raw24;
- custom then entered 708 naturally from caller main+0x7725D0 and never reached 710;
- no type10/11 was found within P118A's +/-32 global-index radius for the custom samples.

Important correction:
P118A +/-32 is only a GLOBAL RECORD CENSUS. It is NOT a proven logical action707
block boundary. Therefore "no type10 +/-32" must not be turned directly into
"the whole action707 block lacks type10".

What P118B adds
---------------
P118B keeps the same boot-safe whole-function trampoline at main+0x3F4BC0.
At the exact focused caller return main+0x77B5AC, static v1.70 proof shows X19
still contains the actor:
  0x77B588 MOV X19,X0
  0x77B58C LDRH W0,[actor+0xB9E4]
  0x77B590 BL 0x3F4B00
  0x77B5A8 BL 0x3F4BC0

P118B logs:
- direct actor pointer from live X19;
- direct [actor+0xB9E4] cursor;
- pointer-derived event index and equality checks;
- exact global event table count/base and cursor distance from table end;
- global container halfwords +A8/+AA/+AC;
- current event name through statically-proven main+0x3F4B60 index->name accessor;
- +/-32 neighboring records with name, raw type and stable record fields.

This separates:
A) cursor identity/instrumentation mismatch;
B) cursor valid but near global-table edge;
C) custom selected data/name family differs from successful control;
D) nearby type10/11 exists, after which same-block ownership still needs proof.

Safety
------
- READ ONLY.
- One new trampoline only: main+0x3F4BC0.
- Native Orig(event_x0) executes exactly once on each runtime path.
- No write to actor+0xB9E4 or event records.
- No branch patch, session create, state write/map, force708, force710.
- No char281 gameplay branch.
- P50 victim-safe VIS_SHADOW / CTRL14_SHADOW remain intact.

Build
-----
python3 verify_p118b_source.py \
&& git add -A \
&& git commit -m "P118B exact event cursor and table identity census" \
&& git push

Expected verifier tail:
push_enabled_workflows ['build-subsdk9-p118b.yml']
p118a_workflow_disabled PASS
P118B_DROPIN_SOURCE_VERIFY=PASS

Artifact:
NSC-P118B-event-table-identity-readonly

Test
----
1. Fresh launch.
2. One successful vanilla/control UJ cinematic.
3. One custom Tobi UJ until the usual absorbed/stuck failure.
4. Do not recover with shuriken/jutsu.
5. Wait ~2 seconds, stop, save the full log.

Required boot marker:
[NSC:P118B] READY ... probe_ok=1

Key runtime markers:
[NSC:P118B] CURSOR ... cursor=... ptr_idx=... count=... end_delta=... raw=... name='...'
[NSC:P118B] REC ... center=... d=... idx=... raw=... name='...'

Analyze:
python3 analyze_p118b_log.py uzuy_log.txt

Interpretation guard
--------------------
Even if +/-32 REC rows contain no type10/11, DO NOT claim a logical block lacks
cinematic type10 until block ownership/boundaries are proven from data structure
semantics. P118B's job is to prove exact cursor/table identity and expose names /
record-family structure so the next back-slice is chosen from evidence.
