# NSC2Switch / UltimateStormAPI Port
# MASTER CHECKPOINT — R71
Date: 2026-09-22

======================================================================
0. PURPOSE
======================================================================

Project:
Porting / reconstructing UltimateStormAPI / MovesetPlus compatibility
for Naruto x Boruto Ultimate Ninja Storm Connections on Nintendo Switch.

Primary target:
Nintendo Switch
Storm Connections update 1.70

Build ID:
48ece454b61412b9fb46fab2be3f5ef7b2804f39

Current main objective:
Make custom/mod characters use their Ultimate Jutsu correctly,
especially while already awakened, without character-specific hacks.

Primary reproducer:
Custom Tobi / Madara-derived mod actor, compiled character ID 281.

FINAL SOLUTION MUST NOT BE TOBI-SPECIFIC.

This checkpoint supersedes scattered assumptions from older experimental
builds. Historical results remain useful evidence but may not be active
architecture.


======================================================================
1. CURRENT DEVELOPMENT ENVIRONMENT
======================================================================

Primary environment:
Android Termux.

NO Ubuntu/proot required for current workflow.

Repository root:
  /storage/emulated/0/Downloads

Important files:
  overlay/source/program/nsc_cpk_bridge.cpp
  overlay/source/program/nsc_cpk_bridge.hpp
  overlay/source/program/main.cpp

Git branch:
  main

Build system:
GitHub Actions

Compiler/toolchain:
devkitPro / devkitA64

Pinned exlaunch:
  commit 229bbd6

Current build process:
Termux edits source
  ->
git commit/push
  ->
GitHub Actions devkitA64 build
  ->
artifact contains paired main + subsdk9.

Do not require local devkitPro in Termux.


======================================================================
2. CURRENT MAIN FILES / HASHES
======================================================================

Restore / vanilla 1.70 main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

Current paired-main lineage uses source-parity patch:
main+0x7F2A9C

Vanilla:
  BD001FE0
  STR S0,[SP,#0x1C]

Patched:
  D503201F
  NOP

Known P65/P67 paired main SHA256:
1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0

Build ID must remain:
48ece454b61412b9fb46fab2be3f5ef7b2804f39


======================================================================
3. NON-NEGOTIABLE PROJECT RULES
======================================================================

DO NOT:
- hardcode char == 281 as gameplay fix;
- hardcode Tobi-only logic;
- patch donor 57 -> 281;
- force action 700;
- convert action 445 -> 700;
- force E94 = 0x87;
- force F58 globally;
- map MovesetPlus selector1 to native selector8;
- restore raw native Event236 handling;
- resurrect old 0x7E1404 forced-tail patch;
- assume PC RVA is directly valid on Switch;
- assume similar address delta proves semantic homolog;
- write actor+0x12A24 / PC actor+0x12A3C blindly;
- use unsafe delayed raw actor-pointer workers;
- call a mid-function BLR manually from C++ and assume ABI parity.

Every gameplay write must have:
1. static proof,
2. runtime proof,
3. native behavior preservation,
4. generic/data-driven policy.

Evidence labels used in this project:

PROVEN RUNTIME
PROVEN STATIC
SOURCE-PROVEN / SOURCE-DERIVED
INFERENCE
HYPOTHESIS


======================================================================
4. MOD / DATA CONTEXT
======================================================================

Known mods merged historically:
- Isshiki Moveset v1.2.1
- Tobi (Madara)
- Yahiko
- Toneri Otsutsuki

Tobi custom:
source ID 280
compiled Switch custom ID 281

Special condition:
281 -> COND_2DNZ

Important:
Final architecture may add more mod characters.
Nothing may depend specifically on ID 281.


======================================================================
5. ORIGINAL / HISTORICAL SYMPTOMS
======================================================================

Earlier symptoms included:
- damage worked but model could become white / low-poly;
- HUD corruption;
- enemy disappearance;
- some characters unhittable;
- opponent HUD awakening behavior;
- Tobi Kamui UJ did not transition correctly to cinematic;
- when Tobi became enemy-UJ victim he could disappear and become
  uncontrollable after cinematic;
- awakening availability inconsistent.

Corrected symptom interpretation:

Tobi own UJ:
- not a hard crash;
- opponent could get caught in Kamui;
- Tobi own UJ did not correctly hand off to cinematic.

Tobi as victim:
- battle continued;
- Tobi could become invisible / unplayable after enemy UJ;
- not a crash.

These are separate problems:
A. own UJ admission / routing
B. own UJ cinematic handoff
C. victim-UJ restore safety
D. awakening control/eligibility


======================================================================
6. IMPORTANT EARLY ARCHITECTURE RESULTS
======================================================================

Alpha14b:
control baseline PASS.

V20D:
enemy not hittable.

V25:
PASS.

V26:
read-only PASS.

V27A:
FAIL.

V33A:
PASS.

Historical Ougi neutral detours around:
0x7E1404
0x7E13E4

could make enemy unhittable.

These addresses must not be reused casually.


======================================================================
7. P1–P4 OUGI / PARAM RESULTS
======================================================================

P1 SPECIALCOND_BOUNDARY_A:
general PASS.

P2 DATADRIVEN_MERGED_PARAMS:
battle normal.
Tobi UJ still no cinematic handoff.
Awakening still unavailable.

P3 OUGI_DATA_DRIVEN_GATE:
FAIL:
Tobi as victim of enemy UJ disappeared.

P3B OUGI_DATA_ONLY_CONTROL:
same victim failure even without Ougi hook.

P4A NATIVE_OUGI_TAIL_RESTORE:
same victim failure.

Conclusion:
old Ougi 0x7E13E4/0x7E1404 was not necessary cause of victim bug.

ROMFS P2 -> P3B:
only ougiAwakeningParam changed:
[3105]
to
[3105,281]

10 other param files identical.

specialCondParam remained:
282 records
281 -> COND_2DNZ


======================================================================
8. EVENT236 / VICTIM-UJ ROOT
======================================================================

Failing victim sequence included Event236 operations:

0x0F disable_control
...
0x03 change_skill
0x0C visibility
0x0E enable_control

Postcondition:
Tobi invisible + unplayable.

P34A established causality:
native Switch Event236 misinterpreted custom MovesetPlus Event236 semantics.

Important result:
RAW NATIVE EVENT236 MUST NOT BE RESTORED.

P50 introduced victim-safe handling / shadow semantics.

P50 remains required baseline infrastructure.

P50 protects custom Event236 operations including critical control /
visibility semantics so enemy UJ victim restoration remains stable.


======================================================================
9. SOURCE-PROVEN MOVESETPLUS CONTROL SEMANTICS
======================================================================

MovesetPlus source proves:

selector 1:
Ultimate Jutsu control

selector 15:
Awakening control

selector 18:
Chakra Shuriken

selector 19:
Tilt

PC source stores semantic UJ latch approximately at:
actor+0x12A3C

PC source stores Awakening semantic approximately at:
actor+0x12A80

These PC offsets ARE SEMANTIC ORACLES ONLY.

DO NOT transplant them to Switch.

Interesting source quirk:
Enable selector19 falls through and also enables selector1/UJ.

Jutsu Selector is a DIFFERENT subsystem.

me_change_skill:
type0 = Jutsu1
type1 = Jutsu2
type2 = Ultimate Jutsu skill index

Do not confuse:
UJ skill selection
with
UJ permission / input eligibility.


======================================================================
10. OUGI AWAKENING SOURCE MODEL
======================================================================

PC UltimateStormAPI 1.70 has two distinct mechanisms for
Ultimate Jutsu while awakened:

A)
PC A33C60:
NOP of a local scalar store.

Switch strongest structural mapping:
main+0x7F2A9C

P65+ paired main currently applies:
BD001FE0 -> D503201F

B)
PC A20C00 policy/wrapper:
native predicate first,
then OugiAwakeningParam membership can force true.

Conceptual source contract:

native = original(actor)

if IsOugiAwakeningCharID(character):
    return true

return native

Important:
the second policy half is NOT yet correctly ported to Switch.

Historical audit R67B labeled A20C00 tail structural homolog around
0x7E13E4/0x7E1404 as proven structurally.

DO NOT misread this:
that did NOT prove a Switch actor->bool policy entry at 0x7E1404.

Old forced tail patch already failed and remains forbidden.

A33 address-distance extrapolation predicted ~0x7DFA3C for A20,
but P68 inspection showed 0x7DFAxx is complex EA0/EA4/EA8
state/timer logic, not a simple actor->bool wrapper.

Therefore:
PC->Switch constant address delta is NOT a valid mapping method.


======================================================================
11. CHARACTER / ACTION STATE FACTS
======================================================================

Actor fields:

+0xE54:
character ID

+0xE94:
active action/state

+0xE98:
previous state

+0xE9C:
queued/requested state

State engine:
main+0x7A811C family reads E9C/E94.

Activation around:
0x7A8438

Behavior:
old E94 -> E98
requested -> E94

Request gateways around:
0x7A89A4 / 0x7A8A9C.


Vanilla ordinary jutsu:
E94 = 77 / 0x4D
action 445

Tobi XA:
E94 = 77
action 445

Tobi XXA currently:
E94 = 77
action 445

Vanilla Ultimate Jutsu:
E94 = 135 / 0x87
action 700

Native vanilla UJ progression observed:
700
-> 707
-> 710
-> 711
-> 712
-> 713
-> 714
-> 740


Known action callsites:

Tobi / ordinary 445:
PlayAction caller return around:
0x7B4B30
callsite:
0x7B4B2C

Vanilla action700:
PlayAction caller return:
0x7E35EC
callsite:
0x7E35E8


======================================================================
12. P57 / P58 / P59 RESULTS
======================================================================

P57:
central setter diagnostics.

P58:
proved action 445 / 700 were already selected before PlayAction.

Therefore:
PlayAction is downstream of root.

P59:
action/mode tracing.

Vanilla XA:
E94=77
action445

Vanilla UJ:
E94=135
action700

Tobi XA:
E94=77
445

Tobi XXA:
E94=77
445

Conclusion:
Tobi XXA diverges BEFORE active state/action selection.


======================================================================
13. NATIVE CONTROL GETTER / SETTER
======================================================================

Native getter:
main+0x7C6280

Native setter:
main+0x7C65B0

When x0 = actor+0x228:
storage appears around:
actor+0x650 + selector*4

P60:
mapped semantic selector1 -> native selector8.

FAIL.

P62:
persistent selector8 true.

Result:
chakra-charge / action148 / repeated sound behavior.

Conclusion:
native selector8 is a different control domain.

Never reuse selector8 for UJ.


======================================================================
14. F58 HISTORY
======================================================================

Candidate F58 entry:
main+0x7D3138

Historical P61 forced it:
did not solve Tobi.

P63 runtime:
vanilla UJ reached F58.

Important runtime caller:
return LR = main+0x7F46B8.

Static disassembly later proved actual invocation:

0x7F46A4 LDR X8,[X19]
0x7F46A8 MOV X0,X19
0x7F46AC MOV W1,WZR
0x7F46B0 LDR X8,[X8,#0xF58]
0x7F46B4 BLR X8
0x7F46B8 CBZ W0,...

Thus F58 is a VIRTUAL actor-specific predicate,
not one universal concrete implementation.

Status:
F58 may be UJ eligibility-related,
but is NOT the MovesetPlus selector1 semantic itself.


======================================================================
15. P64F SEMANTIC BRIDGE
======================================================================

P64 introduced generic actor-local semantic state:

P64SetSemanticUltimateJutsu(actor, enabled)
P64QuerySemanticUltimateJutsu(actor)

Semantic state tracks:
actor pointer
character ID
enabled mask

Ultimate Jutsu bit:
1 << 1

Event236 selector1 enable:
sets semantic UJ true.

Event236 selector1 disable:
sets semantic UJ false.

PROVEN RUNTIME:
Tobi Event236 selector1 reaches semantic state.

Typical marker:
[NSC:P64F] UJ_SEM_SET ... enabled=1

This is a major proven result.

P64 also hooked helper:
main+0x7ABE9C

That helper statically queries native selector1:

0x7ABF28 ADD X0,X19,#0x228
0x7ABF2C MOV W1,#1
0x7ABF30 BL  0x7C6280

P64 original exact allowed callers:
0xC76C4
0xC76F0
0xC78D4

Hardware P64F:
UJ_SEM_SET occurred.
UJ_SEM_GATE did NOT occur on relevant Tobi input route.

Conclusion:
semantic producer works.
P64 consumer was not the active Tobi route.


======================================================================
16. P65A
======================================================================

P65 retained:
P50 victim safety
semantic selector1 state
P57/P59 diagnostics

P65 disabled active P64 0x7ABE9C consumer.

Paired-main source parity:
0x7F2A9C NOP.

P65 hooked concrete F58 implementation 0x7D3138
with active caller LR 0x7F46B8.

Runtime:
vanilla char reached P65 F58 hook.

Tobi did not.

Tobi remained:
requested=445
PlayAction445
E94=77

Conclusion:
Tobi diverges before concrete F58 route.


======================================================================
17. P66A — IMPORTANT FAILED ARCHITECTURE
======================================================================

Static proof:

0x7F46A4 LDR X8,[X19]
0x7F46A8 MOV X0,X19
0x7F46AC MOV W1,WZR
0x7F46B0 LDR X8,[X8,#0xF58]
0x7F46B4 BLR X8
0x7F46B8 CBZ W0,...

P66 attempted inline hook at BLR 0x7F46B4.

Callback manually called actor-specific function pointer from X8,
then wrote:
W0 = native || semantic.

RESULT:
VANILLA UJ BROKE.

Example:
native=1 / ret=1
but game later selected index/action191 instead of normal UJ.

Reason:
replacing BLR with C++ inline callback was NOT ABI-equivalent.

Likely destruction/clobber differences:
caller-saved registers
NZCV / FP state / ABI state
LR / compiler expectations
other hidden side effects.

RULE:
NEVER repeat manual mid-function virtual BLR replacement.

P66 is historical only.
Never install it again.


======================================================================
18. P67A — CURRENT SAFE BASELINE
======================================================================

P67 removed:
P66 inline virtual call bridge
P65 concrete F58 active hook

P67 returned to native/trampoline architecture.

P67 additionally allowed semantic helper caller:
main+0x7F4730

Static:

0x7F4728 MOV X0,X19
0x7F472C BL  0x7ABE9C
0x7F4730 CBNZ W0,...

Inside 0x7ABE9C:
native selector1 getter exists.

P67 runtime:

Vanilla UJ:
NORMAL AGAIN.

Observed:
requested=700
E94=135
PlayAction700
route=UJ

Tobi:
semantic selector1 still set.

But:
requested=445
PlayAction445
E94=77

No relevant UJ_SEM_GATE occurred for Tobi.

Conclusion:
Tobi diverges before this consumer path too.

CURRENT SAFE GAMEPLAY BASELINE:
P67A.

Do not modify P67 gameplay behavior until a better upstream consumer
is proven.


======================================================================
19. P68 STATIC SWEEP
======================================================================

A33 source-parity anchor:

PC:
A33C60

Switch:
0x7F2A9C

Delta-only prediction for PC A20C00:
~0x7DFA3C

Inspection of 0x7DFAxx showed:
complex state/timer/update code;
EA0/EA4/EA8 handling;
virtual calls;
E94 and many combat-state branches.

It does NOT look like the simple PC actor->bool OugiAwakening wrapper.

Conclusion:
constant RVA delta prediction rejected.


P68 ranked active boolean predicates.

Candidate 0x7EA644 was inspected.

Callsite:
0x7F4B68 MOV X0,X19
0x7F4B6C BL  0x7EA644
0x7F4B70 CBZ W0,...

0x7EA644:
complex combat eligibility function;
checks E94, opponent E94, internal state block,
multiple helpers and vtable functions.

Caller proceeds toward state #0x85 family.

Conclusion:
0x7EA644 is NOT current UJ 0x87 selection root.
Candidate rejected.


======================================================================
20. P69 — DIRECT STATE 0x87 SEARCH
======================================================================

P69 scanned battle/input region for textual '#0x87'.

IMPORTANT:
19 reported hits are NOT 19 UJ state assignments.

The scanner matched substrings, so false positives include:
#0x870
#0x876
addresses/functions containing 0x87xxxx
etc.

Relevant true state-related hits:

A)
0x7AF6C8:
MOV W1,#0x87
then actor vtable+0xF98 call.

This is a state/action application path,
not yet proven active player input decision root.

B)
0x7D0150:
SUB W8,W8,#0x87
then range checks.

This reads/handles existing 0x87-family state.
It is downstream.

C) MOST IMPORTANT:
0x7F47B8:
MOV W21,#0x87

This is inside the ACTIVE PLAYER INPUT CLASSIFIER.

This is now the strongest direct static anchor for UJ selection.


======================================================================
21. ACTIVE UJ CLASSIFIER — CURRENT BEST MAP
======================================================================

Known region:
main+0x7F4404 ...

Important sequence:

0x7F46A4 LDR X8,[X19]
0x7F46A8 MOV X0,X19
0x7F46AC MOV W1,WZR
0x7F46B0 LDR X8,[X8,#0xF58]
0x7F46B4 BLR X8
0x7F46B8 CBZ W0,0x7F4738

Success-ish branch:

0x7F46BC MOV X0,X19
0x7F46C0 MOV W1,WZR
0x7F46C4 BL 0x7D2DE4
0x7F46C8 CBNZ W0,0x7F4784
0x7F46CC B 0x7F47B4

Alternate path begins:

0x7F4738 ...
...
0x7F477C BL 0x7D2DE4
0x7F4780 CBZ W0,0x7F47B4

0x7F4784 MOV X0,X20
0x7F4788 MOV W1,#8
0x7F478C BL 0x7C6280
0x7F4790 CBNZ W0,0x7F47B4

then another actor predicate / distance-like test:
0x7F4794...
0x7F47A0 BLR X8
...
0x7F47B0 B.GE 0x7F4890

UJ selection block:

0x7F47B4 MOV W25,WZR
0x7F47B8 MOV W21,#0x87
0x7F47BC LDR X8,[X19]
0x7F47C0 MOV X0,X19
0x7F47C4 LDR X8,[X8,#0x1480]
0x7F47C8 BLR X8

THIS IS CURRENT ROOT FRONTIER.

Question is no longer:
"Which function looks like UJ?"

Question is now:
"Which exact earlier branch prevents Tobi from reaching
0x7F47B4 / MOV W21,#0x87?"


======================================================================
22. WHAT P65/P66/P67 PROVED ABOUT TOBI ROUTE
======================================================================

P65:
Tobi did not reach concrete vanilla F58 implementation.

P66:
hook at exact 0x7F46B4 callsite broke vanilla;
however Tobi did not produce the expected relevant UJ call behavior.

P67:
Tobi did not reach the active 0x7F472C selector1 helper branch.

Together this strongly indicates:

Tobi diverges BEFORE / around the early classifier path leading to
0x7F46A4.

Therefore root is still upstream from state87 selection.

Do not patch after state87 selection.


======================================================================
23. KNOWN NOT-ROOT / CLOSED PATHS
======================================================================

Do not reopen without new contradictory evidence:

- PlayAction
- central action setter
- action 445 -> 700 conversion
- E94 forcing
- E9C forcing
- state87 forcing
- native selector8
- F58 global override
- old Ougi 0x7E13E4 force
- old 0x7E1404 tail override
- P66 BLR inline replacement
- raw native Event236
- PC actor+0x12A3C direct transplant
- Switch actor+0x12A24 guessed write
- char281-specific gameplay branch
- donor57 alias
- address-delta-only PC->Switch mapping


======================================================================
24. VICTIM SAFETY MUST REMAIN
======================================================================

Any future UJ fix MUST preserve P50 behavior.

Regression test after every gameplay build:

Tobi as victim of vanilla enemy UJ:
- cinematic completes;
- Tobi remains visible;
- controls return;
- battle continues;
- no disappearance;
- no permanent disable control.

Do not solve own-UJ bug by breaking victim-UJ again.


======================================================================
25. CURRENT EVIDENCE STATUS
======================================================================

PROVEN RUNTIME:
- P50 victim safety works as current baseline.
- Event236 selector1 reaches P64 semantic UJ state.
- Tobi XXA currently produces 445 / E94 77.
- Vanilla UJ produces 700 / E94 135.
- P66 breaks vanilla despite returning native=1.
- P67 restores vanilla UJ.
- P67 Tobi still 445.

PROVEN STATIC:
- main Build ID / paired main fingerprints.
- 0x7F2A9C source-parity NOP location.
- 0x7F46B4 actor virtual +0xF58 call.
- 0x7F472C calls 0x7ABE9C.
- 0x7ABE9C contains native selector1 getter.
- 0x7F47B8 explicitly selects W21=0x87.
- 0x7EA644 is complex and leads toward non-0x87 family.

SOURCE-PROVEN:
- MovesetPlus selector1 = Ultimate Jutsu control.
- selector15 = Awakening.
- OugiAwakeningParam is separate policy for UJ while awakened.
- PC implementation has two components:
  A33C60 patch + A20C00 membership/native predicate wrapper.

INFERENCE:
- Tobi likely fails one upstream player-input classifier condition
  before state87 block.
- OugiAwakening policy may still be required because Tobi is already
  awakened.

HYPOTHESIS:
- one or more early branches in 0x7F4404..0x7F46A0 rejects custom /
  awakened actor before normal UJ selection.
- exact branch is not yet proven.


======================================================================
26. CURRENT ACTIVE BASELINE
======================================================================

ACTIVE GAMEPLAY BUILD:
P67A

Expected READY marker:
[NSC:P67A] READY

P67 should remain baseline until next target has runtime proof.

P65:
historical/manual only.

P66:
historical/manual only.
DO NOT deploy.

P64:
historical semantic evidence.

P50:
required underlying victim-safe subsystem.


======================================================================
27. CURRENT FRONTIER AFTER R69
======================================================================

Strongest target:

main+0x7F47B8
  MOV W21,#0x87

This is the exact active UJ state-selection anchor.

NEXT TASK:
perform a backward control-flow slice to identify all immediate
predecessor conditions that permit or reject arrival at:

0x7F47B4
0x7F47B8

Then isolate the smallest branch set that differs between:

Vanilla XA
Vanilla UJ
Tobi XA
Tobi XXA

Only after that:
one targeted runtime probe or functional semantic compatibility hook.

NO broad tracing.


======================================================================
28. NEXT DECISION RULE
======================================================================

A future gameplay patch is allowed only if:

1. the target is structurally upstream of 0x7F47B8;
2. runtime proves Tobi actually reaches the relevant decision;
3. vanilla UJ native behavior remains untouched;
4. semantic state is generic/data-driven;
5. no action/state forcing is used;
6. P50 victim safety remains active.


======================================================================
29. MINIMUM HARDWARE TEST MATRIX
======================================================================

For each new meaningful build:

Case A:
vanilla character XA
Expected:
ordinary jutsu / 445 family.

Case B:
vanilla character UJ
Expected:
0x87 -> action700 -> native UJ sequence.

Case C:
Tobi XA
Expected:
ordinary jutsu / 445.

Case D:
Tobi XXA / intended UJ
Current broken:
445.
Target:
native UJ admission path, NOT forced action700.

Case E:
Tobi as enemy-UJ victim
Expected:
visible + playable after cinematic.

Case F:
second match / rematch
Expected:
no lifecycle corruption.


======================================================================
30. IMPORTANT REMINDERS
======================================================================

- Tobi starts already awakened.
  Do not tell tester to "activate awakening first".

- Do not treat absence of UJ cinematic as crash.

- Do not combine victim-UJ and own-UJ root causes.

- Do not assume a helper is active just because static call exists.

- Do not infer a Switch homolog from address proximity alone.

- Do not replace native BLR semantics with a C++ manual function call.

- Keep source generic for future mod characters.

- Prefer one decisive hardware run over many broad traces.

- Every new source edit should be made in Termux and committed to Git.

- GitHub Actions is build machine only.

- Historical files/checkpoints should not be deleted.
  Disable old workflow auto-push instead.

- Never claim a build fixes UJ until hardware shows native UJ route.

- Native UJ success criterion is NOT merely return=1.
  It must progress into native state/action flow.


======================================================================
31. HISTORICAL IMPORTANT ARTIFACTS
======================================================================

P64F build kit:
R73_P64F_UJ_SEMANTIC_BRIDGE_BUILD_KIT.zip

Historical SHA256:
c0df0e55c0d33d974197b773e364dfb2e239029c97991ecccce2bb7246cb139d

P67 current successful GitHub artifact:
NSC-P67A-active-selector1-consumer-bridge

P67 build status:
SUCCESS

P67 gameplay result:
vanilla UJ normal
Tobi UJ still fails to 445

Do not confuse build success with gameplay success.


======================================================================
32. MASTER SUMMARY
======================================================================

Current known chain:

MovesetPlus Event236 selector1
        |
        v
P64 semantic UJ state
        |
        |  PROVEN WORKING
        v
???????????????????????????
Switch active input policy
        |
        v
main+0x7F47B8
MOV W21,#0x87
        |
        v
native requested state
        |
        v
E94=0x87
        |
        v
PlayAction700
        |
        v
native UJ sequence

For Tobi the break is currently somewhere BEFORE the
0x7F47B8 state-selection block.

That exact break is the next target.



======================================================================
33. FILE / ARTIFACT RETRIEVAL POLICY FOR FUTURE CHATS
======================================================================

IMPORTANT INSTRUCTION FOR EVERY FUTURE ASSISTANT:

This project already has a large history of source packages, logs,
compiled artifacts, checkpoints, audit reports, scripts, params,
CPKs, ExeFS dumps, and previous experiments.

DO NOT immediately ask the user to upload an old file again.

Before requesting any previously-used file:

1. Search files already available in the ChatGPT conversation and
   persistent Library.

2. Search by:
   - exact filename when known;
   - build name such as P50, P59, P64F, P65A, P66A, P67A;
   - checkpoint revision;
   - artifact name;
   - relevant address / subsystem;
   - project keywords such as:
     NSC2Switch
     UltimateStormAPI
     Tobi
     Ougi
     Event236
     UJ
     MovesetPlus
     condition
     CPK
     ExeFS.

3. For broad content retrieval:
   use semantic file search first.

4. For an exact phrase/address inside a known file:
   use exact find/read on that file.

5. If a named historical file is not attached in the current chat,
   search the persistent Library before asking the user for it.

6. Search BOTH current conversation files and Library when either
   could contain the required artifact.

7. Do NOT substitute web search for project files that should already
   exist in conversation/Library.

8. If multiple historical versions exist:
   prefer the newest checkpoint or newest proven artifact unless this
   checkpoint explicitly identifies an older build as the required
   control.

9. Do NOT assume similarly-named files are identical.
   Verify filename, version, relevant markers, SHA256, Build ID, or
   source contents where available.

10. If file content is needed to make a technical conclusion:
    inspect the actual file. Do not answer from filename alone.

11. If a Library file needs local binary/programmatic processing:
    materialize/copy the actual Library file into the working
    environment first. Never invent a local sandbox path.

12. Preserve evidence labels:
    PROVEN RUNTIME
    PROVEN STATIC
    SOURCE-PROVEN / SOURCE-DERIVED
    INFERENCE
    HYPOTHESIS

13. Never claim a historical artifact was byte-for-byte verified unless
    that exact verification was actually completed.

14. When continuing this project in a new chat:
    search for this MASTER CHECKPOINT first, then search for the latest
    runtime log and latest active build source/artifact before making a
    new patch.


KNOWN HISTORICAL SEARCH KEYS:

Master / audit:
- NSC2Switch_MASTER_CHECKPOINT
- Audit Teknis R73.1 Source-Resolved
- R67B_OUGI_CONSUMER_PROOF
- alpha14c

Victim safety:
- P50
- Event236
- victim UJ

State / action diagnostics:
- P57
- P58
- P59

Semantic UJ:
- P64F
- UJ_SEM_SET
- UJ_SEM_GATE

F58:
- P63
- P65A

Failed virtual-call architecture:
- P66A
- UJ_VCALL_GATE

Current safe baseline:
- P67A
- active-selector1-consumer-bridge

Current static frontier:
- P69_FIND_STATE87
- P70_STATE87_BACKSLICE
- P71_STATE_SELECTOR_MAP


======================================================================
34. LOCAL MASTER CHECKPOINT STORAGE POLICY
======================================================================

Canonical local checkpoint directory:

/storage/emulated/0/Downloads

Canonical current checkpoint file:

/storage/emulated/0/Downloads/
NSC2Switch_MASTER_CHECKPOINT_2026-09-22_R69.1.md

Rules:

- Every new master checkpoint revision must be created in
  /storage/emulated/0/Downloads first.

- Do not make the only authoritative checkpoint inside a temporary
  container, sandbox, /tmp directory, or GitHub Actions workspace.

- Git may contain a second persistent copy, but the Termux Downloads
  copy is the user's canonical local working copy.

- New revisions should use explicit names, for example:

  NSC2Switch_MASTER_CHECKPOINT_2026-09-22_R70.md
  NSC2Switch_MASTER_CHECKPOINT_2026-09-22_R71.md

- Never silently overwrite an older major checkpoint.
  Preserve history.

- Small correction revisions may use:
  R69.1
  R69.2
  etc.

- After creating/updating a checkpoint, always print:
  path
  size
  SHA256
  revision marker.

- Important new runtime results must be incorporated into the next
  checkpoint rather than being left only inside chat messages.


======================================================================
35. HANDOFF INSTRUCTION FOR A NEW CHAT
======================================================================

If this project continues in a new ChatGPT conversation:

1. Search Library/conversation for the newest
   NSC2Switch_MASTER_CHECKPOINT first.

2. Read the checkpoint before proposing a patch.

3. Search for the newest active runtime log and relevant source/build
   artifact already stored in Library.

4. Treat the checkpoint as the authoritative project history unless
   newer runtime evidence explicitly supersedes it.

5. Do not restart old hypotheses already marked rejected/forbidden.

6. Do not ask the user to repeat technical history already contained
   in the checkpoint or retrievable project files.

7. Continue from CURRENT FRONTIER / CURRENT NEXT ACTION.

8. Make source modifications through Termux copy/paste scripts whenever
   possible.

9. Use GitHub Actions only as the remote compiler/build machine unless
   there is a specific reason to do otherwise.

10. Keep final gameplay architecture generic and data-driven for future
    custom characters.




======================================================================
36. R70 — STATE87 BACKWARD-SLICE RESULT
======================================================================

P70 script:
P70_STATE87_BACKSLICE.py

P70 result:
P70_STATE87_BACKSLICE=PASS

The active UJ state-selection block is now statically locked:

0x7F47B4  MOV W25,WZR
0x7F47B8  MOV W21,#0x87

This is the strongest current UJ state-selection anchor.


----------------------------------------------------------------------
36.1 DIRECT INCOMING EDGES TO UJ BLOCK
----------------------------------------------------------------------

Exact incoming routes to 0x7F47B4:

1)
0x7F46CC:
B 0x7F47B4

2)
0x7F4780:
CBZ W0,0x7F47B4

3)
0x7F4790:
CBNZ W0,0x7F47B4

4)
natural fallthrough:
0x7F47B0 -> 0x7F47B4


----------------------------------------------------------------------
36.2 F58 TRUE ROUTE
----------------------------------------------------------------------

0x7F46A4 LDR X8,[X19]
0x7F46A8 MOV X0,X19
0x7F46AC MOV W1,WZR
0x7F46B0 LDR X8,[X8,#0xF58]
0x7F46B4 BLR X8
0x7F46B8 CBZ W0,0x7F4738

If F58 returns nonzero:

0x7F46BC MOV X0,X19
0x7F46C0 MOV W1,WZR
0x7F46C4 BL 0x7D2DE4
0x7F46C8 CBNZ W0,0x7F4784
0x7F46CC B 0x7F47B4

Therefore:
F58=true + postgate=false reaches UJ state87 directly.


----------------------------------------------------------------------
36.3 F58 FALSE / ALTERNATE UJ ROUTE
----------------------------------------------------------------------

F58 false does NOT necessarily reject Ultimate Jutsu.

It enters:

0x7F4738 actor virtual +0x1928
...
0x7F477C BL 0x7D2DE4
0x7F4780 CBZ W0,0x7F47B4

If not accepted there:

0x7F4784 MOV X0,X20
0x7F4788 MOV W1,#8
0x7F478C BL 0x7C6280
0x7F4790 CBNZ W0,0x7F47B4

If still not accepted:

0x7F4794 actor virtual +0xDB0
0x7F47A0 BLR X8
0x7F47A4 MOV W8,#0x42C80000
0x7F47A8 FMOV S1,W8
0x7F47AC FCMP S0,S1
0x7F47B0 B.GE 0x7F4890

If comparison is below threshold:
fallthrough reaches:

0x7F47B4 MOV W25,WZR
0x7F47B8 MOV W21,#0x87


IMPORTANT CORRECTION:

F58 is NOT a unique required UJ gate.

There are multiple routes into state87.

Therefore:
forcing F58 globally was conceptually wrong in addition to the previous
runtime failures.


----------------------------------------------------------------------
36.4 PRE-F58 BOOLEAN DECISIONS
----------------------------------------------------------------------

P70 identified these boolean-call decision sites before F58:

0x7F4588 indirect -> CBZ 0x7F4640
0x7F4594 -> 0x8B2D04 -> CBZ 0x7F4A38
0x7F45A8 indirect -> CBZ 0x7F4690
0x7F45E8 -> 0x805BC4 -> CBNZ 0x7F4F10
0x7F45F4 -> 0x7C553C -> CBNZ 0x7F490C
0x7F4608 indirect -> CBZ 0x7F4840
0x7F4624 -> 0x7C5FC0 -> CBZ 0x7F4630
0x7F4634 -> 0x7C5FC0 -> CBNZ 0x7F48E8
0x7F4644 -> 0x8B2B70 -> CBNZ 0x7F4658
0x7F4650 -> 0x8B2C54 -> CBZ 0x7F4590
0x7F465C -> 0x794EC8 -> CBZ 0x7F46A0
0x7F4694 -> 0x7C5FFC -> CBNZ 0x7F4A38

These are NOT all UJ-specific.

Do not patch any of them merely because they occur before state87.


----------------------------------------------------------------------
36.5 CURRENT INTERPRETATION
----------------------------------------------------------------------

PROVEN STATIC:

The player-input classifier selects Ultimate Jutsu state by assigning:

W21 = 0x87

at:
main+0x7F47B8.

PROVEN STATIC:

Several distinct control-flow paths can reach that block.

PROVEN RUNTIME FROM EARLIER BUILDS:

Tobi XXA does not reach the previously traced F58 / selector1-helper
route in the same way vanilla UJ does.

Therefore the remaining root question is:

Which state branch / state assignment is selected for Tobi instead of
the W21=0x87 route?

This is more useful than continuing to rank generic boolean helpers.


======================================================================
37. R70 CURRENT NEXT ACTION — P71
======================================================================

Next static task:

Map every assignment to the state-selection register W21 in the same
player-input classifier.

Also locate where W21 is forwarded into the native state request.

Primary questions:

1. What other literal state values are loaded into W21?
2. Which route corresponds to ordinary jutsu?
3. Where does W21=0x87 converge with other state routes?
4. Which earlier branch selects between ordinary and UJ state?
5. Can a single runtime probe distinguish vanilla UJ from Tobi XXA
   without modifying gameplay?


P71 MUST REMAIN READ-ONLY.

No gameplay source changes yet.

P67A remains the current safe runtime baseline.


======================================================================
38. CHECKPOINT UPDATE RULE FROM R70 ONWARD
======================================================================

After every meaningful static/runtime result:

1. create a NEW master checkpoint revision in:

   /storage/emulated/0/Downloads

2. never leave critical evidence only in chat;

3. include:
   - result;
   - corrections to older assumptions;
   - rejected paths;
   - current active baseline;
   - exact next action;

4. preserve older checkpoint files;

5. print SHA256 after creation;

6. optionally commit checkpoint to Git after local creation;

7. future chats must search existing Library/conversation project files
   before asking the user to re-upload them.





======================================================================
39. R71 — W21 STATE SELECTOR MAP
======================================================================

P71:
P71_STATE_SELECTOR_MAP.py

Result:
P71_STATE_SELECTOR_MAP=PASS


----------------------------------------------------------------------
39.1 IMPORTANT REGISTER-LIFETIME CORRECTION
----------------------------------------------------------------------

W21 is NOT globally a state register throughout the entire classifier.

Examples before the UJ state-selection region:

0x7F461C MOV W21,W0
0x7F462C TBNZ W21,#15,...
0x7F4678 CSET W21,EQ
0x7F4688 ORR W2,W21,W8

Therefore:

Do NOT interpret every W21 value in this function as E94/action state.

The meaning of W21 changes across control-flow/lifetime regions.


----------------------------------------------------------------------
39.2 CONFIRMED UJ STATE SELECTION
----------------------------------------------------------------------

The UJ corridor contains:

0x7F47B4 MOV W25,WZR
0x7F47B8 MOV W21,#0x87

and later:

0x7F4820 MOV W1,W21

This materially strengthens the interpretation that W21 is the selected
state value in this local region.

Thus:

0x87 is a true selected state value here,
not merely a coincidental immediate.


----------------------------------------------------------------------
39.3 ALTERNATE STATE 0x8D
----------------------------------------------------------------------

P71 found:

0x7F47B0 B.GE 0x7F4890

0x7F4890 MOV W21,#0x8D
0x7F4894 MOV W25,#1
0x7F4898 B 0x7F47BC

Therefore state 0x87 and state 0x8D converge at the same downstream
dispatcher beginning at 0x7F47BC.

This means the branch at 0x7F47B0 is NOT simply:

UJ vs ordinary jutsu.

It selects between at least two related state variants:
0x87 and 0x8D.

Do not patch that branch.


----------------------------------------------------------------------
39.4 DYNAMIC STATE-SELECTION ROUTE
----------------------------------------------------------------------

A separate route begins at:

0x7F490C MOV X0,X19
0x7F4910 BL 0x795350
0x7F4914 MOV W21,W0

This is highly significant.

Unlike the literal UJ route:

W21 = 0x87

this route obtains W21 dynamically from helper:

main+0x795350

This helper may select an ordinary or alternate player state.

Its exact semantic is NOT YET PROVEN.

It must be statically audited before runtime instrumentation.


----------------------------------------------------------------------
39.5 OTHER W21 LITERALS
----------------------------------------------------------------------

Other W21 assignments observed:

0x7F4A18 W21=1
0x7F4BF0 W21=2
0x7F4F60 W21=3
0x7F4F98 W21=1
0x7F4FAC W21=-1

These occur in later/different control-flow contexts.

Do NOT interpret these values as E94 states merely because the same
physical register W21 is used.

Register reuse is present.


----------------------------------------------------------------------
39.6 CURRENT STRONGEST STATIC MODEL
----------------------------------------------------------------------

Current model:

                 UJ admission corridor
                         |
                  +------+------+
                  |             |
             local condition    |
                  |             |
              W21=0x87       W21=0x8D
                  |             |
                  +------+------+
                         |
                    0x7F47BC
                         |
                         v
                 common dispatcher


Separate route:

                  0x7F490C
                     |
                     v
                  0x795350
                     |
                     v
                dynamic W21
                     |
                     v
               alternate state flow


The current root question is now:

What does 0x795350 return, and under which branch does execution enter
that dynamic-state route instead of the UJ state87 corridor?


======================================================================
40. R71 NEXT ACTION — P72
======================================================================

P72 is READ ONLY.

Objectives:

1. Recover exact common dispatcher after W21=0x87 / W21=0x8D.
2. Prove how W21 is forwarded to native state request.
3. Audit the body of main+0x795350.
4. Find direct branch references into:
   - 0x7F47BC
   - 0x7F4890
   - 0x7F490C
5. Determine whether 0x795350 can produce ordinary state 0x4D or
   another state that explains Tobi's current route.

No gameplay writes.

P67A remains safe runtime baseline.



END MASTER CHECKPOINT R71
