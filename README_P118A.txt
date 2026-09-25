P118A — EVENT NEIGHBORHOOD / INDEX CENSUS (READ ONLY)
======================================================
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70

Why P118A exists
----------------
P117A proved the custom UJ is missing the cinematic trigger BEFORE session creation:
- successful vanilla action707 dispatches raw event type10;
- custom semantic action707 dispatches raw type15 then raw type24;
- custom never dispatches raw type10/11 before 707->708.

P118A keeps the same boot-safe one-trampoline boundary main+0x3F4BC0 and adds:
- exact global event-record index derived from the 0x60-stride table;
- raw event types at index -4..+4;
- nearest raw type10/11 within index +/-32.

This distinguishes two cases without changing gameplay:
A) type10 exists near the custom cursor but is skipped -> trace cursor/index selection;
B) no type10 exists in the local event block -> trace action707 event-block/data selection.

Safety
------
- READ ONLY.
- One new trampoline only: main+0x3F4BC0.
- Native Orig executes exactly once on every path.
- main+0x3F4B00 is used only as a statically-proven bounds-checked lookup.
- No event cursor write, no branch patch, no session create, no state map/write,
  no force708/710, no char281 gameplay branch.
- P50 victim-safe VIS_SHADOW / CTRL14_SHADOW remain intact.

Build
-----
python3 verify_p118a_source.py \
&& git add -A \
&& git commit -m "P118A census action-event neighborhood" \
&& git push

Expected verifier tail:
push_enabled_workflows ['build-subsdk9-p118a.yml']
p117_workflow_disabled PASS
P118A_DROPIN_SOURCE_VERIFY=PASS

Artifact:
NSC-P118A-event-neighborhood-census-readonly

Test
----
1. One vanilla UJ through a successful cinematic.
2. One custom Tobi UJ until enemy is absorbed/stuck.
3. Do not recover with shuriken/jutsu.
4. Wait a few seconds, exit, save full log.

Boot marker:
[NSC:P118A] READY ... probe_ok=1

Runtime marker:
[NSC:P118A] NEIGH ... idx=... raw=... near10_delta=... m4=... cur=... p4=...
