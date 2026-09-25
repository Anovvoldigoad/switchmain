P110A — CINEMATIC MANAGER PHASE READ-ONLY PROBE

Purpose
- Retire P107/P108 functional state remaps.
- Observe the native type10 UJ/cinematic session manager at main+0x74F954.
- Determine whether custom Tobi reaches manager phase2/phase3 and what paired-actor +0xB968 gate value controls phase2 -> phase3.

Locked facts from P109
- Native state137 request comes through state gateway main+0x7A89A4.
- Exact caller return for native req137: main+0x74FF7C.
- That request is inside phase3 of main+0x74F954.
- Vanilla: request136 @ 0x7E3778 -> state136/action707 -> req137 @ 0x74FF7C -> state137 -> PlayAction710 @ 0x7E6EC8.
- Custom: request136 @ 0x7E3778 -> state136/action707 -> action708 -> request125 @ 0x7EB28C -> 261 -> 74.

Probe design
- Parent: P96.
- Exactly one new whole-function trampoline: main+0x74F954.
- Unique direct caller: BL main+0x74F6AC, LR main+0x74F6B0.
- Read-only. Orig(manager,ctx) is called unchanged exactly once per runtime path.
- No state mapping, no direct actor/state writes, no force708/710, no char281 branch.
- P50 victim-safe Event236 shadows remain preserved.

Runtime records
[NSC:P110A] MGR
  manager phase pre->post, previous phase, team, flag34, manager timers.
[NSC:P110A] LEADER
  leader actor identity/action/E94/E98/E9C/BDA fields pre->post.
[NSC:P110A] PAIRED
  paired actor identity/action/state plus paired +0xB968 pointer/value.
  B968 is dereferenced only when manager pre-phase == 2, matching the native gate use.

Decision matrix
1) Vanilla should show phase progression to phase3, followed by native req137/710 in inherited traces.
2) If custom has no P110 MGR rows during its UJ: type10 manager/session creation/registration is missing upstream.
3) If custom reaches phase2 repeatedly and paired b968 > 1 while vanilla transitions 2->3 with b968 <= 1: exact frontier is the paired B968 gate.
4) If custom reaches phase2 with b968 <= 1 and still does not transition to3: inspect phase2 actor/session lookup/return path.
5) If custom reaches phase3 but no req137: back-slice phase3 setup before 0x74FF6C.

Test
- One fresh boot.
- One successful vanilla UJ.
- One failing custom Tobi UJ.
- Send the complete log and compiled P110A artifact.
