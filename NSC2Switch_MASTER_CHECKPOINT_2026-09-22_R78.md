# NSC2Switch / UltimateStormAPI Port
# MASTER CHECKPOINT — R78
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





======================================================================
41. R72 — DYNAMIC ROUTE CORRECTION
======================================================================

P72:
P72_DYNAMIC_STATE_ROUTE.py

Result:
P72_DYNAMIC_STATE_ROUTE=PASS


----------------------------------------------------------------------
41.1 COMMON 0x87 / 0x8D DISPATCHER
----------------------------------------------------------------------

The literal state routes converge at:

0x7F47BC LDR X8,[X19]
...
0x7F4820 MOV W1,W21
0x7F4824 LDR X8,[X8,#0xDF0]
0x7F4828 BLR X8

For UJ route:

W21 = 0x87

For alternate related route:

W21 = 0x8D

PROVEN STATIC:

The selected literal in W21 is forwarded as argument W1 into the
actor virtual +0xDF0 interface.

Historical static evidence elsewhere in the game also shows +0xDF0
called with literal state-like values such as 0xCC and 0xCD.

Therefore +0xDF0 is strongly consistent with the native
state-transition/request interface.


----------------------------------------------------------------------
41.2 IMPORTANT CORRECTION — 0x795350 IS NOT A STATE SELECTOR
----------------------------------------------------------------------

P72 proved exact body:

0x795350:
    LDR W0,[X0,#0xE64]
    RET

Therefore:

0x795350 is a trivial getter for actor+0xE64.

It is NOT a dynamic state policy function.

The older R71 interpretation:

"0x795350 dynamically chooses ordinary state"

is REJECTED.


----------------------------------------------------------------------
41.3 E64 DATA FLOW
----------------------------------------------------------------------

Immediately before the getter route:

0x7F48E8 BL 0x7983B0
or
0x7F4900 BL 0x798484

then:

0x7F4908 STR W0,[X19,#0xE64]

then:

0x7F490C MOV X0,X19
0x7F4910 BL 0x795350
0x7F4914 MOV W21,W0

Thus W21 receives actor+0xE64.

This proves another register-lifetime transition:

W21 in the literal 0x87/0x8D corridor
    = selected state value

W21 in the 0x7F4914 route
    = E64-derived value / code

Do NOT conflate these lifetimes.


----------------------------------------------------------------------
41.4 E64 SEMANTIC STATUS
----------------------------------------------------------------------

The exact meaning of Switch actor+0xE64 is NOT YET PROVEN.

Do not label it:
- character ID;
- E94 state;
- Ultimate Jutsu state;
- jutsu index;
- MovesetPlus selector1 latch;

without additional proof.

Known source-level jutsu indices on PC use different fields
(E78/E7C/E80 in audited NSC source), so E64 must not be silently
identified with the source Ultimate-Jutsu index field.


----------------------------------------------------------------------
41.5 DYNAMIC ROUTE IS A DIFFERENT SUBSYSTEM
----------------------------------------------------------------------

After W21 receives E64:

0x7F491C BL 0x7AB0C8

then W21 is used arithmetically:

SUB W8,W21,#1
...
MADD ...
...
BL 0x768E84

and later W21 may be reset to zero and forwarded to a different actor
virtual interface:

0x7F4994 MOV W1,W21
0x7F4998 LDR X8,[X8,#0xEA0]
0x7F499C BLR X8

Therefore the 0x7F490C route is NOT the same state-request path as
0x7F47BC -> virtual +0xDF0.

This route is currently classified as a separate action/input
subsystem.


----------------------------------------------------------------------
41.6 DIRECT ESCAPES INTO 0x7F490C
----------------------------------------------------------------------

P72 found direct control-flow into 0x7F490C from:

0x7F45F8 CBNZ W0,0x7F490C
0x7F463C B 0x7F490C
0x7F488C B 0x7F490C
0x7F48FC CBZ W0,0x7F490C

The earliest two are BEFORE the known F58 UJ corridor.

They are now the strongest static frontier:

Gate A:
0x7F45F4 BL 0x7C553C
0x7F45F8 CBNZ W0,0x7F490C

Gate B:
0x7F4634 BL 0x7C5FC0
0x7F4638 CBNZ W0,0x7F48E8
0x7F463C B 0x7F490C

Because Tobi fails to reach the later proven UJ route,
these early escape gates must be understood before any new runtime
patch.


----------------------------------------------------------------------
41.7 CURRENT STATUS
----------------------------------------------------------------------

PROVEN STATIC:
- W21=0x87 is genuine state selection in local UJ corridor.
- W21=0x8D is alternate state selection in same corridor.
- both flow to actor vtable +0xDF0 with W1=selected state.
- 0x795350 is exactly an actor+0xE64 getter.
- W21 is reused for E64 data in the later 0x7F490C route.
- 0x7F490C route is structurally different from +0xDF0 state request.

REJECTED:
- 0x795350 as ordinary-state selector.
- interpreting every W21 assignment as action/state.
- using E64 semantics without proof.

CURRENT SAFE RUNTIME BASELINE:
P67A.

NO gameplay writes introduced by P68-P72.


======================================================================
42. R72 NEXT ACTION — P73 EARLY ESCAPE GATES
======================================================================

P73 remains READ ONLY.

Focus only on the two earliest exits into the non-UJ E64 route:

A)
0x7F45F4 -> 0x7C553C
0x7F45F8 -> 0x7F490C when nonzero

B)
0x7F4634 -> 0x7C5FC0
0x7F4638 / 0x7F463C route choice

Objectives:

1. recover exact argument setup for both calls;
2. inspect exact helper bodies;
3. determine whether either helper is a control/input predicate;
4. determine whether actor or actor+0x228 is being queried;
5. do NOT patch until semantic contract is clear;
6. choose at most ONE narrow runtime probe after static proof.





======================================================================
43. R73 — EARLY ESCAPE GATE AUDIT
======================================================================

P73:
P73_EARLY_ESCAPE_GATES.py

Result:
P73_EARLY_ESCAPE_GATES=PASS


----------------------------------------------------------------------
43.1 GATE A — 0x7C553C
----------------------------------------------------------------------

Active callsite:

0x7F45F0 MOV X0,X20
0x7F45F4 BL 0x7C553C
0x7F45F8 CBNZ W0,0x7F490C

Exact helper:

0x7C553C LDR W0,[X0,#0x6A8]
0x7C5540 RET

From the already-established classifier prologue:

X20 = actor + 0x228

Therefore Gate A reads:

(actor + 0x228) + 0x6A8
= actor + 0x8D0

PROVEN STATIC:
Gate A is a simple 32-bit field getter on the native control/input
sub-object.

NOT PROVEN:
- that actor+0x8D0 is MovesetPlus selector1;
- that it is an Ultimate Jutsu latch;
- that nonzero means UJ disabled;
- that it is safe to write.

Do not patch actor+0x8D0.


----------------------------------------------------------------------
43.2 GATE B — 0x7C5FC0
----------------------------------------------------------------------

Exact helper:

0x7C5FC0 LDR W8,[X0,#0x598]
0x7C5FC4 LDR W9,[X0,#0x404]
0x7C5FC8 TST W9,W8
0x7C5FCC CSET W0,NE
0x7C5FD0 RET

Thus:

return (
    [control+0x598] &
    [control+0x404]
) != 0

With X20 = actor+0x228:

first field:
actor + 0x7C0

second field:
actor + 0x62C

PROVEN STATIC:
0x7C5FC0 is a native bitmask predicate.

It belongs to a family of adjacent helpers testing related input/control
mask banks.

It is NOT source-proven to represent MovesetPlus selector1.


----------------------------------------------------------------------
43.3 IMPORTANT CFG CORRECTION
----------------------------------------------------------------------

The Gate-B region does NOT provide a path onward to F58/UJ.

Sequence:

0x7F4624 BL 0x7C5FC0
0x7F4628 CBZ W0,0x7F4630

if nonzero:
    0x7F462C TBNZ W21,#15,0x7F4900

if execution reaches 0x7F4630:

0x7F4630 MOV X0,X20
0x7F4634 BL 0x7C5FC0
0x7F4638 CBNZ W0,0x7F48E8
0x7F463C B 0x7F490C

Therefore after reaching the second Gate-B test:

true  -> 0x7F48E8
false -> 0x7F490C

Both are alternate/E64 route families.

Neither continues to:

0x7F4640 -> ... -> F58 -> state87

Therefore Gate B is NOT the UJ-admission gate.


----------------------------------------------------------------------
43.4 NEW STRONGEST FORK
----------------------------------------------------------------------

Previous P70 already identified:

0x7F4588 BLR <virtual>
0x7F458C CBZ W0,0x7F4640

This now becomes the strongest control-flow fork.

If W0 == 0:
execution jumps directly to:

0x7F4640

which is upstream of the proven F58/UJ corridor.

If W0 != 0:
execution falls through into:

0x7F4590...
...
Gate A
Gate B
alternate E64 route

Therefore the new precise question is:

Does vanilla UJ take:

0x7F458C -> 0x7F4640

while Tobi XXA falls through into the alternate route?

This must be established before patching anything.


----------------------------------------------------------------------
43.5 P73 CALLER-COUNT SCRIPT LIMITATION
----------------------------------------------------------------------

P73 printed:

0x7C553C direct_callers=0
0x7C5FC0 direct_callers=1

These counts are INVALID / INCOMPLETE.

Reason:

The same P73 output directly proves:

0x7F45F4 BL 0x7C553C

and:

0x7F4624 BL 0x7C5FC0
0x7F4634 BL 0x7C5FC0

Thus the reported census contradicts visible direct calls.

Cause:
wide linear Capstone disassembly over a large mixed code/data region can
stop before later addresses and is not an exhaustive raw-BL reference
scanner.

RULE:
Do not use P73 direct caller counts as evidence.

Future caller census must scan raw aligned ARM64 words / decode each
4-byte instruction independently.


----------------------------------------------------------------------
43.6 CURRENT MODEL AFTER P73
----------------------------------------------------------------------

                             ACTIVE CLASSIFIER
                                    |
                           virtual call @4588
                                    |
                         0x7F458C CBZ W0
                           /                \
                        ZERO               NONZERO
                         |                    |
                         v                    v
                     0x7F4640            0x7F4590...
                         |                    |
                    eligibility            Gate A
                    predicates               |
                         |                  Gate B
                         |                    |
                         v                    v
                    0x7F46A4            E64 route
                       F58
                         |
                         v
                    post-gate
                         |
                         v
                    W21=0x87
                         |
                         v
                 virtual +0xDF0


CURRENT SAFE RUNTIME BASELINE:
P67A.

No gameplay writes were introduced by P68-P73.


======================================================================
44. R73 NEXT ACTION — P74 FORK LOCK
======================================================================

P74 remains READ ONLY.

Objectives:

1. recover exact setup of the virtual call at 0x7F4588;
2. identify its vtable slot;
3. map complete 0x7F4540..0x7F46A4 CFG;
4. prove all paths into 0x7F4640;
5. prove all paths into alternate 0x7F4590 route;
6. inspect 0x7F4640..0x7F46A4 completely;
7. do not use broad caller scans;
8. after static proof, select at most TWO filtered runtime markers:
   - one marker for UJ corridor;
   - one marker for alternate corridor.

No gameplay writes.





======================================================================
45. R74 — UJ FORK LOCK
======================================================================

P74:
P74_UJ_FORK_LOCK.py

Result:
P74_UJ_FORK_LOCK=PASS


----------------------------------------------------------------------
45.1 EXACT EARLY FORK
----------------------------------------------------------------------

The active classifier contains:

0x7F457C LDR X8,[X19]
0x7F4580 MOV X0,X19
0x7F4584 LDR X8,[X8,#0x1288]
0x7F4588 BLR X8
0x7F458C CBZ W0,0x7F4640

Thus:

actor virtual slot +0x1288
returns a bool-like W0.

If W0 == 0:
execution jumps directly to:
0x7F4640

If W0 != 0:
execution falls through to:
0x7F4590

This is the strongest current upstream UJ fork.


----------------------------------------------------------------------
45.2 ZERO SIDE — UJ CORRIDOR
----------------------------------------------------------------------

0x7F4640 MOV X0,X19
0x7F4644 BL 0x8B2B70
0x7F4648 CBNZ W0,0x7F4658

If that returns zero:

0x7F464C MOV X0,X19
0x7F4650 BL 0x8B2C54
0x7F4654 CBZ W0,0x7F4590

Therefore entering 0x7F4640 is necessary for this UJ corridor,
but is NOT sufficient to reach state87.

The corridor can still bounce back into the alternate route at
0x7F4654.

Next:

0x7F4658 MOV X0,X19
0x7F465C BL 0x794EC8
0x7F4660 CBZ W0,0x7F46A0

Then optional logic at 0x7F4664..0x7F468C converges into:

0x7F46A4 F58 setup
0x7F46B4 F58 virtual call
...

and eventually one valid route reaches:

0x7F47B4 MOV W25,WZR
0x7F47B8 MOV W21,#0x87


----------------------------------------------------------------------
45.3 NONZERO SIDE — ALTERNATE CORRIDOR
----------------------------------------------------------------------

If the +0x1288 virtual predicate returns nonzero:

0x7F4590 MOV X0,X19
0x7F4594 BL 0x8B2D04
0x7F4598 CBZ W0,0x7F4A38

The remaining fallthrough performs alternate classifier logic,
including Gate A / Gate B / E64-related handling.

This side does NOT directly branch to 0x7F4640.

One subpath may enter 0x7F4690, but:

0x7F4690 -> 0x7C5FFC
             |
             + nonzero -> 0x7F4A38
             |
             + zero -> 0x7F45B0

and the zero branch returns to Gate A/B alternate handling,
not to 0x7F4640.

Thus the two main early corridors are now structurally separated.


----------------------------------------------------------------------
45.4 RUNTIME PROBE ARCHITECTURE DECISION
----------------------------------------------------------------------

DO NOT inline-hook:

0x7F4588 BLR actor_vtable+0x1288

Reason:

P66 already proved that replacing a mid-function virtual BLR with a
C++ callback can break vanilla behavior even when the returned W0 is
logically identical.

Instead use normal function-entry trampolines on direct helpers.

Candidate ALT marker:

0x8B2D04

Exact active caller:

0x7F4594 BL 0x8B2D04
return LR:
0x7F4598

Candidate UJ-corridor marker:

0x8B2B70

Exact active caller:

0x7F4644 BL 0x8B2B70
return LR:
0x7F4648

Both markers will:
- call Orig first;
- preserve native return;
- never alter gameplay;
- log only when LR matches exact classifier caller;
- remain generic;
- contain no char281 branch.


----------------------------------------------------------------------
45.5 R74 HYPOTHESIS TO TEST
----------------------------------------------------------------------

HYPOTHESIS:

Vanilla UJ:
reaches UJ-corridor marker at return 0x7F4648.

Tobi XXA:
reaches ALT marker at return 0x7F4598 and fails to reach the UJ
corridor.

This is NOT runtime-proven yet.

P75 will test exactly this divergence.


----------------------------------------------------------------------
45.6 P75 SAFETY REQUIREMENTS
----------------------------------------------------------------------

Before creating P75 gameplay binary:

1. verify 0x8B2D04 is a normal hookable function entry;
2. verify 0x8B2B70 is a normal hookable function entry;
3. recover their exact first instruction fingerprints;
4. confirm actor is passed in X0;
5. confirm bool-like return is in W0;
6. inspect current P67 source anchors;
7. do not modify P67 source until those checks pass.

P75 probe itself must have:

NO force87
NO force700
NO selector8
NO actor-field writes
NO char281 gameplay condition
NO raw Event236 restore
NO F58 override
NO inline BLR replacement

CURRENT SAFE RUNTIME BASELINE:
P67A.





======================================================================
46. R75 — FORK PROBE PREFLIGHT
======================================================================

P75_PROBE_PREFLIGHT.py

Result:
P75_PROBE_PREFLIGHT=PASS

Target Build ID:
48ece454b61412b9fb46fab2be3f5ef7b2804f39


----------------------------------------------------------------------
46.1 ALT CORRIDOR PROBE TARGET
----------------------------------------------------------------------

Classifier:

0x7F458C CBZ W0,0x7F4640
0x7F4590 MOV X0,X19
0x7F4594 BL 0x8B2D04
0x7F4598 CBZ W0,0x7F4A38

Exact active return:
0x7F4598

Function entry:
0x8B2D04

Fingerprint first 8 words:

F81D0FFE
A90157F6
A9024FF4
5282E208
72A00028
AA0003F3
B8686814
97FBE29D

Observed prologue:

0x8B2D04 STR X30,[SP,#-0x30]!
0x8B2D08 STP X22,X21,[SP,#0x10]
0x8B2D0C STP X20,X19,[SP,#0x20]

Actor argument X0 is immediately saved:

0x8B2D18 MOV X19,X0

Caller consumes W0 as bool-like result.


----------------------------------------------------------------------
46.2 UJ CORRIDOR PROBE TARGET
----------------------------------------------------------------------

Classifier:

0x7F4640 MOV X0,X19
0x7F4644 BL 0x8B2B70
0x7F4648 CBNZ W0,0x7F4658

Exact active return:
0x7F4648

Function entry:
0x8B2B70

Fingerprint first 8 words:

F81E0FFE
A9014FF4
9108A014
AA0003F3
AA1403E0
52800101
97FC4DBE
340000A0

Observed prologue:

0x8B2B70 STR X30,[SP,#-0x20]!
0x8B2B74 STP X20,X19,[SP,#0x10]
0x8B2B78 ADD X20,X0,#0x228
0x8B2B7C MOV X19,X0

Caller consumes W0 as bool-like result.


----------------------------------------------------------------------
46.3 SOURCE BASELINE CONFIRMATION
----------------------------------------------------------------------

Current source still exposes:

kUjSemanticConsumerOffset = 0x7ABE9C

P64QuerySemanticUltimateJutsu()

MainRelativeOffset()

P64SemanticUjConsumerHook

InstallP67AActiveSelector1ConsumerBridge()

main.cpp still calls:

nsc::InstallP67AActiveSelector1ConsumerBridge()

Thus P67A remains the active source lineage.

P75 probe will be added on top of P67A rather than rebuilding from an
older branch.


----------------------------------------------------------------------
46.4 IMPORTANT ABI SAFETY HOLD
----------------------------------------------------------------------

DO NOT install the P75 runtime trampolines yet.

Reason:

The preflight dump proves:
- valid function entries;
- actor in X0 at entry;
- bool-like W0 consumed by classifier;
- exact fingerprints;
- exact caller return addresses.

But the preflight windows did NOT prove the full reachable CFG of both
functions.

Before declaring either function's C++ trampoline ABI as:

uint32_t(void* actor)

we must verify that no reachable path depends on incoming X1-X7 or
other caller-provided arguments.

This rule exists specifically to avoid repeating the P66 ABI mistake.


======================================================================
47. R75 NEXT ACTION — ABI LOCK
======================================================================

P75_ABI_LOCK remains READ ONLY.

Only two functions are analyzed:

ALT:
0x8B2D04

UJ corridor:
0x8B2B70

Objectives:

- reconstruct reachable CFG from each entry;
- stop at RET / terminal branch;
- identify all return sites;
- list references to X1-X7 / W1-W7;
- determine whether those registers are initialized internally before
  use;
- prove whether actor-only trampoline ABI is safe.

Only after ABI LOCK passes may runtime probes be installed.

Planned runtime markers:

[NSC:P75] ALT_CORRIDOR
exact caller return = 0x7F4598

[NSC:P75] UJ_CORRIDOR
exact caller return = 0x7F4648

Both must:
- call Orig;
- preserve native return exactly;
- perform zero gameplay writes;
- contain no char281 branch;
- contain no force87;
- contain no force700;
- contain no selector8 override;
- contain no F58 override.

CURRENT SAFE BASELINE:
P67A.





======================================================================
48. R76 — P75 ABI LOCK COMPLETE
======================================================================

P75_ABI_LOCK.py

Result:
P75_ABI_LOCK=PASS


----------------------------------------------------------------------
48.1 UJ CORRIDOR TARGET ABI
----------------------------------------------------------------------

Target:
main+0x8B2B70

Reachable instructions:
41

Return sites:
3

0x8B2B9C
0x8B2BF0
0x8B2C10

Observed X1-X7 / W1-W7 references:

0x8B2B84 MOV W1,#8
0x8B2BC4 MOV W1,#2

Both W1 values are defined internally.

No incoming X1-X7/W1-W7 dependency was found.

One path performs a tail branch to:

0x7C5FC0

after restoring the target function's stack frame.

This is consistent with forwarding a bool-like return.


----------------------------------------------------------------------
48.2 ALT CORRIDOR TARGET ABI
----------------------------------------------------------------------

Target:
main+0x8B2D04

Reachable instructions:
113

Return sites:
1

0x8B2E88

Observed additional argument-register references are internally defined:

W1:
- literal #6
- actor field +0x7CC
- literal #9
- zero
- CSEL-generated action/index

W2:
- literal #1

No incoming X1-X7/W1-W7 dependency was found.

Floating-point comparisons using S0 occur only after internal helper
calls that produce S0.

Therefore no incoming FP argument dependency is currently indicated.


----------------------------------------------------------------------
48.3 ABI VERDICT
----------------------------------------------------------------------

PROVEN STATIC for both probe targets:

Input:
X0 = actor

Return:
W0 = bool/integer-like result

Safe trampoline contract:

uint32_t(void* actor)

Targets:

ALT:
0x8B2D04

UJ:
0x8B2B70

This is materially different from P66.

P66 replaced a mid-function indirect BLR and manually reproduced the
call, which was not ABI-equivalent.

P76A will hook normal function entries and call Orig(actor), preserving
the original target function and native return value.


----------------------------------------------------------------------
48.4 EXACT ACTIVE CALLERS
----------------------------------------------------------------------

ALT corridor:

0x7F4590 MOV X0,X19
0x7F4594 BL 0x8B2D04
0x7F4598 CBZ W0,...

Expected caller return:
0x7F4598


UJ corridor:

0x7F4640 MOV X0,X19
0x7F4644 BL 0x8B2B70
0x7F4648 CBNZ W0,...

Expected caller return:
0x7F4648


----------------------------------------------------------------------
48.5 P76A RUNTIME PROBE CONTRACT
----------------------------------------------------------------------

P76A is READ-ONLY.

Two new normal function-entry trampolines:

ALT_CORRIDOR:
main+0x8B2D04

UJ_CORRIDOR:
main+0x8B2B70

Each hook:

1. records caller return;
2. records actor identity;
3. records semantic selector1 state;
4. records E94/E9C before/after;
5. calls Orig(actor);
6. returns Orig result unchanged.

Absolutely NO:

- force87
- force700
- selector8 override
- F58 override
- actor-field write
- char281 gameplay branch
- inline BLR replacement
- raw Event236 restore.

P67A remains the behavioral baseline underneath the probe.


======================================================================
49. R76 RUNTIME HYPOTHESIS
======================================================================

Primary hypothesis:

Vanilla UJ:
    UJ_CORRIDOR caller=0x7F4648

Tobi XXA:
    ALT_CORRIDOR caller=0x7F4598

If this is observed, divergence before F58 becomes:

PROVEN RUNTIME.

If Tobi reaches UJ_CORRIDOR too, continue inside:

0x8B2B70
    ->
0x8B2C54
    ->
0x794EC8
    ->
F58

without returning to the already rejected early-fork hypothesis.


======================================================================
50. NEXT ACTION
======================================================================

Build P76A read-only runtime fork probe.

Minimum runtime matrix:

Vanilla:
- ordinary XA sanity
- one successful UJ

Tobi:
- ordinary XA sanity
- XXA reproducer

Victim safety:
- no regression to disappearance/unplayable behavior.

After runtime log:
update MASTER CHECKPOINT to R77 before any functional gameplay patch.





======================================================================
51. R76.1 — P76A SOURCE PATCH VERIFIED
======================================================================

P76A source patch has been applied on top of the P67A source lineage.

Public installer:

InstallP76AForkRuntimeProbe()

Static source verification:

1. P67A baseline is installed FIRST:

   InstallP67AActiveSelector1ConsumerBridge();

2. ALT target is fingerprint-gated:

   main+0x8B2D04

   expected:
   F81D0FFE
   A90157F6
   A9024FF4
   5282E208
   72A00028
   AA0003F3
   B8686814
   97FBE29D

3. UJ target is fingerprint-gated:

   main+0x8B2B70

   expected:
   F81E0FFE
   A9014FF4
   9108A014
   AA0003F3
   AA1403E0
   52800101
   97FC4DBE
   340000A0

4. Probe hooks are installed only if BOTH fingerprints pass.

5. Installer reports:

   [NSC:P76A] READY

   with:
   baseline_p67=1
   readonly=1
   preserve_orig=1
   no_force87=1
   no_force700=1
   no_selector8=1
   no_f58_override=1
   no_char281_branch=1

6. main.cpp now enters P76A rather than independently calling P67A.
   P76A itself installs P67A, so there must be exactly ONE baseline
   installation path.

7. No gameplay-return override is intended by P76A.

STATUS:

PROVEN STATIC:
- target fingerprints;
- target ABI actor->W0;
- installer ordering;
- fail-closed target installation;
- exact active caller returns:
  ALT = 0x7F4598
  UJ  = 0x7F4648.

NOT YET PROVEN RUNTIME:
- probe boot safety;
- LR caller filtering;
- vanilla/Tobi corridor divergence.

NEXT:
Build P76A and perform runtime comparison.

Do NOT introduce a functional UJ fix before the P76A runtime result.





======================================================================
52. R76.2 — FINAL SOURCE SANITY BEFORE BUILD
======================================================================

Final P76A source sanity result:

main.cpp:
    exl::hook::Initialize();
    nsc::InstallP76AForkRuntimeProbe();

Header contains:
    InstallP67AActiveSelector1ConsumerBridge();
    InstallP76AForkRuntimeProbe();

Runtime installation chain:

main.cpp
    ->
InstallP76AForkRuntimeProbe()
    ->
InstallP67AActiveSelector1ConsumerBridge()

Therefore P67A remains underneath P76A and is not independently
installed twice by active source.

Occurrences in *.pre_p76a files are backup-only and do not represent
runtime installation.

git diff --check:
PASS / no whitespace errors reported.

P76 ALT hook source confirmed:
- calls Orig(actor)
- stores native result
- logs read-only diagnostics
- returns native result unchanged.

UJ hook source contains Orig(actor), but final return-ret line still
requires one focused textual sanity check because the previous grep
window ended before the complete callback.

IMPORTANT REPOSITORY NOTE:

The working tree contains many historical scripts, logs, checkpoints,
and backup directories as untracked files.

DO NOT use:
    git add .

Only explicitly stage the intended P76A source files, workflow, and
current checkpoint.

Also verify build-subsdk9-p76a.yml exists before commit because the
previous git status output did not visibly show that workflow file.

No gameplay behavior has been changed beyond adding read-only probes.





======================================================================
53. R76.3 — P76A FINAL SOURCE SANITY
======================================================================

Final source sanity:

ACTIVE INSTALL PATH:
main.cpp:
    nsc::InstallP76AForkRuntimeProbe();

P76A installer:
    InstallP67AActiveSelector1ConsumerBridge();

Therefore:
main -> P76A -> P67A

No active duplicate P67A installation exists.

ALT probe:
    ret = Orig(actor)
    log ALT_CORRIDOR / ALT_OTHER
    return ret

UJ probe:
    ret = Orig(actor)
    log UJ_CORRIDOR / UJ_OTHER
    return ret

Thus both runtime probes preserve native return values.

git diff --check:
PASS.

SOURCE STATUS:
P76A source is READY FOR BUILD.

CURRENT BLOCKER:
.github/workflows/build-subsdk9-p76a.yml
does not currently exist.

Do NOT modify gameplay source.

NEXT:
Create P76A workflow from the known-good P67A workflow while preserving:
- pinned exlaunch commit 229bbd6
- devkitpro/devkita64:latest
- existing source overlay procedure
- existing artifact packaging structure.

After workflow validation:
stage ONLY intended P76A files and R76.3 checkpoint,
then commit/push.

R77 remains reserved for P76A runtime evidence.





======================================================================
54. R76.4 — P76A WORKFLOW CLONE CORRECTION
======================================================================

A first P76A workflow was generated by mechanically replacing:

P67A -> P76A
p67a -> p76a

in the known-good P67A workflow.

This is NOT ready to commit.

The generated workflow now references:

verify_p76a_kit.py
prepare_exlaunch_p76a.sh
README_P76A.txt
p76a_final.elf

These files / contracts have NOT yet been established.

The known-good P67A workflow originally uses:

verify_p67a_kit.py
prepare_exlaunch_p67a.sh
README_P67A.txt
p67a_final.elf

IMPORTANT:

Do not rename helper script references merely for cosmetic build
identity.

The prepare script may itself control ELF_EXTRACT and other build
configuration, so workflow and helper script names must remain
contract-consistent.

P76A C++ source remains valid and unchanged.

NEXT:

Audit only:
- verify_p67a_kit.py
- prepare_exlaunch_p67a.sh
- README_P67A.txt
- relevant P67A workflow references.

Then choose one of:

A) reuse proven P67 helper scripts unchanged where they are generic;

or

B) create deliberate P76 helper variants only where P67-specific
   assertions actually require changes.

Do NOT push the current mechanically-renamed P76A workflow.

R77 remains reserved for runtime evidence.





======================================================================
55. R76.5 — P76A BUILD-HELPER CONTRACT RESOLVED
======================================================================

Helper audit completed.


----------------------------------------------------------------------
55.1 verify_p67a_kit.py
----------------------------------------------------------------------

The P67A verifier is NOT reusable unchanged.

It explicitly checks for:

InstallP67AActiveSelector1ConsumerBridge

[NSC:P67A] READY

header declaration:
void InstallP67AActiveSelector1ConsumerBridge();

and, critically, main.cpp:

nsc::InstallP67AActiveSelector1ConsumerBridge();

P76A intentionally changes the active main entry to:

nsc::InstallP76AForkRuntimeProbe();

Therefore the verifier requires a deliberate P76A variant.

Architecture decision:

Create verify_p76a_kit.py FROM the proven P67 verifier.

Keep all P67 baseline checks that remain valid.

Change only the expected main entrypoint to P76A and add explicit
P76A invariants:
- two read-only corridor hooks;
- exact offsets;
- exact fingerprints;
- Orig(actor);
- return ret;
- P76A installer wraps P67A exactly once;
- main calls P76A exactly once;
- main does not independently call P67A.


----------------------------------------------------------------------
55.2 prepare_exlaunch_p67a.sh
----------------------------------------------------------------------

This helper is fundamentally generic.

It copies:

main.cpp
nsc_cpk_bridge.cpp
nsc_cpk_bridge.hpp

and patches config.mk:

LOAD_KIND := Module
PROGRAM_ID := 0100FA10190A0000

Its only P67-specific build identity is:

ELF_EXTRACT := $(PWD)/p67a_final.elf

and a cosmetic P67 echo message.

There is NO technical requirement to rename this ELF for P76A.

Decision:

REUSE prepare_exlaunch_p67a.sh unchanged.

P76A workflow will therefore continue to build:

exlaunch/p67a_final.elf

The ELF filename is build plumbing only and does not define runtime
behavior.


----------------------------------------------------------------------
55.3 README
----------------------------------------------------------------------

README_P67A describes the P67 semantic selector1 experiment and is not
sufficient documentation for P76A.

Create:

README_P76A.txt

documenting:
- P67A behavioral baseline preserved;
- P76A ALT/UJ corridor probes;
- read-only / preserve-Orig contract;
- exact runtime test matrix.


----------------------------------------------------------------------
55.4 WORKFLOW CORRECTION
----------------------------------------------------------------------

The mechanically generated P76 workflow currently references
nonexistent:

prepare_exlaunch_p76a.sh
p76a_final.elf

These references must be reverted to:

prepare_exlaunch_p67a.sh
p67a_final.elf

The workflow DOES use the new:

verify_p76a_kit.py
README_P76A.txt

Artifact identity remains P76A.

Collect-stage binary checks must require BOTH:

[NSC:P76A] READY

and:

[NSC:P67A] READY

because P76A deliberately wraps the complete P67A behavioral baseline.


----------------------------------------------------------------------
55.5 FILE POLICY
----------------------------------------------------------------------

Do not stage historical backups/audits/checkpoints.

Expected P76A commit files:

.github/workflows/build-subsdk9-p76a.yml
verify_p76a_kit.py
README_P76A.txt
overlay/source/program/main.cpp
overlay/source/program/nsc_cpk_bridge.cpp
overlay/source/program/nsc_cpk_bridge.hpp
NSC2Switch_MASTER_CHECKPOINT_2026-09-22_R76.5.md

prepare_exlaunch_p67a.sh remains unchanged and is reused.

R77 remains reserved for actual P76A runtime evidence.





======================================================================
56. R76.6 — P76A BUILD PREFLIGHT COMPLETE
======================================================================

Local P76A verifier:

P67_SOURCE_VERIFY=PASS
P67_ACTIVE_CALL_VERIFY=PASS
P67_SELECTOR1_VERIFY=PASS
P67_MAIN_PREREQ_VERIFY=PASS

DEPLOY_MAIN_SHA256:
1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0

P76A_EXTENSION_VERIFY=PASS
P76A_STATIC_VERIFY=PASS


----------------------------------------------------------------------
56.1 REQUIRED BUILD FILES
----------------------------------------------------------------------

PASS:
verify_p76a_kit.py

PASS:
prepare_exlaunch_p67a.sh

PASS:
README_P76A.txt

PASS:
.github/workflows/build-subsdk9-p76a.yml


----------------------------------------------------------------------
56.2 FINAL WORKFLOW CONTRACT
----------------------------------------------------------------------

Workflow:

Build NSC P76A Read-Only UJ Fork Runtime Probe

Toolchain:
devkitpro/devkita64:latest

Pinned exlaunch:
229bbd6

Verifier:
verify_p76a_kit.py

Prepare helper:
prepare_exlaunch_p67a.sh

IMPORTANT:
Reuse of prepare_exlaunch_p67a.sh is intentional.

It is generic build plumbing except for the internal ELF filename:

p67a_final.elf

P76A deliberately retains that internal ELF filename.

This does NOT mean the runtime build is P67A.

Runtime source entry is P76A.


----------------------------------------------------------------------
56.3 ELF BUILD ASSERTIONS
----------------------------------------------------------------------

The P76A workflow requires the final ELF to contain:

[NSC:P76A] READY
[NSC:P67A] READY
[NSC:P64F] UJ_SEM_GATE
[NSC:P64F] UJ_SEM_SET
[NSC:P50A] READY

This proves P76A is layered on the required behavioral baseline.


----------------------------------------------------------------------
56.4 ARTIFACT IDENTITY
----------------------------------------------------------------------

Artifact:

NSC-P76A-readonly-uj-fork-probe

Documentation:

README_P76A.txt


----------------------------------------------------------------------
56.5 WORKFLOW REFERENCE AUDIT
----------------------------------------------------------------------

Forbidden nonexistent references:

prepare_exlaunch_p76a.sh
p76a_final.elf
README_P67A.txt

Result:

P76_WORKFLOW_STALE_REFERENCE=PASS

None are present in the final P76A workflow.


----------------------------------------------------------------------
56.6 SOURCE / REPOSITORY SANITY
----------------------------------------------------------------------

git diff --check:
PASS

P76A probes remain:

READ ONLY
Orig-preserving
generic
no char281 gameplay branch

NO:
- force87
- force700
- selector8 override
- F58 override
- inline BLR replacement
- actor gameplay-field write
- raw Event236 restore


----------------------------------------------------------------------
56.7 CURRENT STATUS
----------------------------------------------------------------------

P76A source:
STATIC PASS

P76A ABI:
STATIC PASS

P76A fingerprints:
STATIC PASS

P76A verifier:
PASS

P76A workflow:
PASS

P76A GitHub Actions build:
NOT YET RUN

P76A runtime:
NOT YET TESTED


======================================================================
57. R76.6 NEXT ACTION
======================================================================

Stage ONLY the seven intended P76A files.

Commit and push.

Run GitHub Actions P76A.

If build fails:
preserve and inspect the exact failing step before changing source.

If build passes:
deploy P76A and perform the minimum runtime matrix:

1. vanilla XA sanity
2. vanilla UJ
3. Tobi XA sanity
4. Tobi XXA
5. victim-UJ safety regression check

Primary runtime question:

Does vanilla UJ reach:

UJ_CORRIDOR caller_off=0x7F4648

while Tobi XXA reaches:

ALT_CORRIDOR caller_off=0x7F4598

?

R77 is RESERVED for actual P76A build/runtime evidence.

No functional UJ fix before that evidence.





======================================================================
58. R77 — P76A RUNTIME RESULT
======================================================================

Artifact:
NSC-P76A-readonly-uj-fork-probe.zip

Runtime log:
uzuy_log(16).txt


----------------------------------------------------------------------
58.1 P76A INSTALLATION
----------------------------------------------------------------------

Runtime:

P50A READY
P67A READY

P76A READY:
baseline_p67=1
probe_ok=1
alt=0x8B2D04
alt_return=0x7F4598
uj=0x8B2B70
uj_return=0x7F4648
readonly=1
preserve_orig=1
no_force87=1
no_force700=1
no_selector8=1
no_f58_override=1
no_char281_branch=1

Therefore P76A boot/runtime installation:
PROVEN RUNTIME PASS.


----------------------------------------------------------------------
58.2 VANILLA UJ — NEW STRONG PROOF
----------------------------------------------------------------------

Vanilla actor char272:

Immediately before native UJ:

P76A:
UJ_CORRIDOR
ret=1
caller_off=0x7F4648
E94=1
E9C=0

timestamp:
104.591252

Then:

P57:
requested=700
E94=135

timestamp:
104.591437

Then:

P59:
PLAY_ACTION index=700

timestamp:
104.592140

Therefore:

PROVEN RUNTIME:

main+0x8B2B70 returning 1 at the active classifier caller is directly
correlated with native UJ admission leading to action700.

This target is no longer merely a generic function in the UJ corridor.
A positive return is meaningful to native UJ acceptance.


----------------------------------------------------------------------
58.3 TOBI RESULT REMAINS 445
----------------------------------------------------------------------

Tobi char281 side0:

requested=445
PlayAction445
E94=77 / 0x4D

This reproduces the known failure under P76A.

No functional regression/fix occurred.


----------------------------------------------------------------------
58.4 IMPORTANT P76A PROBE LIMITATION
----------------------------------------------------------------------

P76A corridor probes were too hot.

ALT logger reached:

n=511
timestamp=101.458758

UJ logger reached:

n=511
timestamp=111.724067

The actual later Tobi side0 attempt occurred around:

timestamp=156.857553

Therefore BOTH P76 log budgets were exhausted before the real Tobi
XXA attempt.

There are no P76A corridor records for the later side0 Tobi actor.

Thus:

DO NOT claim:

"Tobi XXA runtime-proven to take ALT instead of UJ"

from this log.

That hypothesis remains NOT PROVEN.


----------------------------------------------------------------------
58.5 CLASSIFIER MODEL CORRECTION
----------------------------------------------------------------------

ALT_CORRIDOR and UJ_CORRIDOR are hot recurring classifier paths.

They are NOT mutually exclusive one-shot routes corresponding directly
to one button press.

Vanilla actors can execute both paths repeatedly during ordinary battle
frames.

The important signal is therefore not:

"corridor was seen"

but:

"what result/state transition occurred at the actual acceptance frame"


----------------------------------------------------------------------
58.6 SEMANTIC SELECTOR1
----------------------------------------------------------------------

Event236 selector1 continues to establish:

UJ_SEM_SET enabled=1

for custom actor char281.

Therefore semantic MovesetPlus selector1 state remains working.

The missing behavior is downstream of semantic establishment.


----------------------------------------------------------------------
58.7 ARTIFACT AUDIT
----------------------------------------------------------------------

Patched main SHA256:

1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0

subsdk9 SHA256:

58265537450a990fd75d4a0c3b3460ae488c02fa73af8e1d1c2a383946c3819b

restore main SHA256:

2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

Payload hashes match artifact SHA256SUMS.

Packaging issue:

SHA256SUMS.txt contains a checksum entry for SHA256SUMS.txt itself.
That self-entry fails after the file changes.

This is a packaging metadata bug only.

Do not treat it as subsdk9/main corruption.

Future workflow:
do not include SHA256SUMS.txt in its own checksum manifest.


======================================================================
59. R77 NEXT ACTION — LOW-VOLUME ACCEPTANCE PROBE
======================================================================

Do NOT patch gameplay yet.

P77 must retain P67 behavioral baseline and normal function-entry
trampolines.

The probe must avoid per-frame logging saturation.

Primary target remains:

main+0x8B2B70

because P76 proved:

ret=1
    ->
native requested700

P77 goal:

capture the exact return/state behavior around:
- vanilla UJ acceptance;
- Tobi XXA failure.

Recommended logging architecture:

per-actor transition/dedup logging instead of every invocation.

Log when at least one changes:
- UJ helper ret
- E94
- E9C
- semantic selector1 state
- actor identity/lifecycle

Always log any UJ helper ret=1.

ALT helper should be secondary and likewise transition-deduplicated.

Do not use global n<512 hot-loop counters as the primary capture gate.

Minimum comparison:

Vanilla:
UJ helper ret 0 -> 1
then requested700

Tobi:
determine exact UJ helper ret/state sequence during XXA
before requested445.

Only after that result should a functional policy overlay be designed.





======================================================================
60. R77.1 — P77A SOURCE SANITY COMPLETE
======================================================================

P77A source patch has been applied successfully.

ACTIVE main.cpp:

    nsc::InstallP77AAcceptanceProbe();

P76A is NOT installed from main.cpp.

Confirmed:

P77_MAIN_P76_DISABLED=PASS

P77 installer:

    InstallP67AActiveSelector1ConsumerBridge();

then fingerprint-gates:

    main+0x8B2B70

and installs only:

    P77UjAcceptanceHook

P76 ALT/UJ hot-loop probes are deliberately not installed.


----------------------------------------------------------------------
60.1 P77 CALLBACK CONTRACT
----------------------------------------------------------------------

Target:

main+0x8B2B70

Active return:

main+0x7F4648

Static ABI remains:

uint32_t(void* actor)

Callback executes:

    ret = Orig(actor)

and finally:

    return ret

Native result is therefore preserved exactly.


----------------------------------------------------------------------
60.2 P77 LOGGING MODEL
----------------------------------------------------------------------

Unlike P76A, P77A has no global n<512 hot-loop cap.

At the exact active caller it logs when at least one is interesting:

- semantic selector1 is active;
- native helper return is nonzero;
- E94 changes;
- E9C changes.

Any positive return from the exact active caller is therefore retained.

This is designed to survive until the real Tobi XXA attempt rather
than exhausting the probe budget during earlier battle frames.


----------------------------------------------------------------------
60.3 ACTIVE SOURCE CHAIN
----------------------------------------------------------------------

Runtime installation architecture:

main
    ->
InstallP77AAcceptanceProbe
    ->
InstallP67AActiveSelector1ConsumerBridge
    ->
P77UjAcceptanceHook

P76 diagnostic code remains present in source only as historical code.

It is NOT part of the active installation chain.


----------------------------------------------------------------------
60.4 SOURCE SANITY RESULT
----------------------------------------------------------------------

Header contains:

InstallP67AActiveSelector1ConsumerBridge()
InstallP76AForkRuntimeProbe()
InstallP77AAcceptanceProbe()

Only P77A is called by active main.cpp.

git diff --check:
PASS

No gameplay writes introduced.

NO:
- force87
- force700
- selector8 override
- F58 override
- char281 gameplay branch
- inline BLR replacement
- raw Event236 restore.


======================================================================
61. R77.1 NEXT ACTION
======================================================================

Create P77A build verifier, README, and workflow.

Reuse unchanged:

prepare_exlaunch_p67a.sh

and its internal:

p67a_final.elf

P77 workflow must require ELF markers:

[NSC:P77A] READY
[NSC:P67A] READY
[NSC:P64F] UJ_SEM_SET
[NSC:P50A] READY

P76A READY must NOT be required because P76A is not actively
installed.

After local verifier PASS:

build P77A.

Then run:

1. vanilla UJ
2. Tobi XXA

Primary runtime evidence required:

Vanilla:
P77 UJ_ACCEPT ret=1
then requested700 / PlayAction700

Tobi:
capture semantic=1 helper result immediately before requested445.

No functional policy patch before this result.





======================================================================
62. R77.2 — P77A BUILD PREFLIGHT PASS
======================================================================

P77A build preflight completed with fail-fast shell:

set -euo pipefail

Therefore the final PASS marker cannot be reached after an earlier
verification failure.


----------------------------------------------------------------------
62.1 VERIFIER RESULT
----------------------------------------------------------------------

P67_SOURCE_VERIFY=PASS

P67_ACTIVE_CALL_VERIFY=PASS
0x7F472C -> 0x7ABE9C

P67_SELECTOR1_VERIFY=PASS
0x7ABF2C = W1,#1
0x7ABF30 -> 0x7C6280

P67_MAIN_PREREQ_VERIFY=PASS
0x7F2A9C = D503201F

DEPLOY_MAIN_SHA256:

1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0

P76A_EXTENSION_VERIFY=PASS
P76A_SOURCE_HISTORY_VERIFY=PASS

IMPORTANT:
P76 verification is historical/source verification only.
P76 is NOT installed by active main.cpp.

P77A_EXTENSION_VERIFY=PASS
P77A_STATIC_VERIFY=PASS


----------------------------------------------------------------------
62.2 ACTIVE INSTALLATION
----------------------------------------------------------------------

Active main.cpp:

    nsc::InstallP77AAcceptanceProbe();

Result:

P77_MAIN_CHAIN=PASS

P76A is not active from main.


----------------------------------------------------------------------
62.3 BUILD FILES
----------------------------------------------------------------------

Present:

verify_p77a_kit.py
prepare_exlaunch_p67a.sh
README_P77A.txt
.github/workflows/build-subsdk9-p77a.yml

prepare_exlaunch_p67a.sh reuse is intentional.

Internal build ELF remains:

p67a_final.elf

This is build plumbing only.


----------------------------------------------------------------------
62.4 WORKFLOW CONTRACT
----------------------------------------------------------------------

Required markers / dependencies:

verify_p77a_kit.py
prepare_exlaunch_p67a.sh
p67a_final.elf
[NSC:P77A] READY
[NSC:P67A] READY
[NSC:P64F] UJ_SEM_SET
[NSC:P50A] READY
README_P77A.txt
pinned exlaunch 229bbd6

Result:

P77_WORKFLOW_REQUIRED_MARKERS=PASS


Forbidden stale references:

prepare_exlaunch_p77a.sh
p77a_final.elf
[NSC:P76A] READY
README_P76A.txt

Result:

P77_WORKFLOW_STALE_REFERENCE=PASS


----------------------------------------------------------------------
62.5 SOURCE SANITY
----------------------------------------------------------------------

git diff --check:
PASS

P77A remains diagnostic only.

Native helper result is preserved:

    ret = Orig(actor)
    return ret

No gameplay force introduced.


----------------------------------------------------------------------
62.6 BUILD PREFLIGHT VERDICT
----------------------------------------------------------------------

P77_BUILD_PREFLIGHT=PASS

Status:

P77A source                  PASS
P77A static ABI              PASS
P77A fingerprint             PASS
P77A verifier                PASS
P77A workflow                PASS
P77A local build preflight   PASS

GitHub Actions build:
NOT YET RUN

Runtime:
NOT YET TESTED


======================================================================
63. R77.2 NEXT ACTION
======================================================================

Stage ONLY intended P77A release files.

Do NOT stage:
- historical scripts
- .pre_p76a backups
- .pre_p77a backups
- helper generator scripts
- older checkpoint revisions

Then commit/push and run GitHub Actions P77A.

If build fails:
fix only the exact compiler/build-contract issue.

If build passes:
deploy P77A and perform runtime comparison.

Required runtime proof:

VANILLA:
P77 UJ_ACCEPT ret=1
then requested700 / PlayAction700

TOBI:
semantic=1 at actual XXA attempt
capture native helper return immediately before requested445.

No gameplay policy change before that result.





======================================================================
64. R78 — P77A RUNTIME ROUTE EXCLUSION
======================================================================

Inputs:

uzuy_log(17).txt
NSC-P77A-uj-acceptance-probe.zip


----------------------------------------------------------------------
64.1 ARTIFACT AUDIT
----------------------------------------------------------------------

ZIP SHA256:

cfe42c0aafab044f6d94a236191c8e2ac70b6dd26df2b073a011735560204def

ZIP CRC:
PASS

Patched main:

1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0

P77A subsdk9:

0a1264f084e891d7d539e2d2f99375f73796946d172a61ff05a5f21ab31afef2

Restore main:

2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

README:

b1f56d4d2b8c1ec60cdf3cc525a6a62b76b5545521ba87d7c3d5b5f50d2be1b8

All real payload entries match SHA256SUMS.

Packaging metadata issue remains:

SHA256SUMS.txt contains a checksum for itself.

Recorded self SHA:
36300e952cf8fef4a83344e0f8cdf06253f945cae7b67d7867385b1012c1619e

Actual final SHA:
0a3453426f4b2caed300b31ca10b9e47e3423be19b7c8b22cd224b4bbb88abb4

This is NOT payload corruption.

Future workflow must exclude SHA256SUMS.txt from its own manifest.


----------------------------------------------------------------------
64.2 P77A INSTALLATION
----------------------------------------------------------------------

Runtime:

P50A READY
P67A READY

P77A READY:

baseline_p67=1
probe_ok=1
uj=0x8B2B70
uj_return=0x7F4648
semantic_focus=1
positive_ret_always_log=1
global_hot_cap=0
alt_probe_installed=0
readonly=1
preserve_orig=1

Therefore P77A runtime installation:
PASS.


----------------------------------------------------------------------
64.3 VANILLA SUCCESS REFERENCE
----------------------------------------------------------------------

Vanilla actor:

char=91
actor=0x3b183c5000

At timestamp:

103.093654

P77:

UJ_ACCEPT
semantic=0->0
ret=1
caller_off=0x7F4648
E94=1->1
E9C=0->0

Then:

103.093976
requested=700

Delta:

0.000322 seconds

Then:

103.094951
PlayAction700

Delta from P77 positive result:

0.001297 seconds

Therefore:

PROVEN RUNTIME:

main+0x8B2B70 ret=1 is part of the successful native UJ admission path
immediately preceding action700.


----------------------------------------------------------------------
64.4 TOBI SEMANTIC STATE
----------------------------------------------------------------------

Tobi player:

actor=0x3acd502000
side=0
char=281

Semantic selector1 repeatedly establishes:

enabled=1

Attempt 1:

UJ_SEM_SET:
155.475710

requested445:
156.742016

delta:
1.266306 sec


Attempt 2:

UJ_SEM_SET:
163.876343

requested445:
165.142575

delta:
1.266232 sec


Attempt 3:

UJ_SEM_SET:
172.276642

requested445:
172.475621

delta:
0.198979 sec


All three attempts:

requested445
PlayAction445
E94=77 / 0x4D


----------------------------------------------------------------------
64.5 CRITICAL P77 RESULT
----------------------------------------------------------------------

The entire runtime log contains only two P77A records:

1. P77A READY
2. one vanilla UJ_ACCEPT char91 ret=1

There is NO:

P77A UJ_ACCEPT char281

and NO:

P77A UJ_OTHER_POSITIVE char281

during the Tobi attempts.

P77 callback logging contract:

At exact caller 0x7F4648 it logs if:

semantic_pre == true
OR semantic_post == true
OR ret != 0
OR E94 changes
OR E9C changes.

Tobi semantic state is repeatedly set to true.

No Event236 op15 appears in the runtime log.

Actor pointer and char identity remain stable.

Therefore the prior hypothesis:

"Tobi reaches main+0x8B2B70 but native helper returns 0"

is rejected by this runtime.

Strong runtime conclusion:

Tobi's failing route diverges BEFORE the active
main+0x7F4644 -> main+0x8B2B70 UJ-helper call.


----------------------------------------------------------------------
64.6 CONSEQUENCES
----------------------------------------------------------------------

The following downstream targets are no longer primary root-cause
candidates for this failure:

0x8B2C54
0x794EC8
F58 gate
state87 selector
post-0x8B2B70 UJ gates

Tobi does not reach the probed UJ helper during the failing route.

Do NOT:

force 0x8B2B70 return1
force state87
force action700
force F58
restore P66 inline BLR architecture.


----------------------------------------------------------------------
64.7 PRIMARY UPSTREAM CANDIDATE
----------------------------------------------------------------------

Existing static CFG:

0x7F4588 BLR virtual+0x1288
0x7F458C CBZ W0,0x7F4640

nonzero:
    0x7F4590
    0x7F4594 BL 0x8B2D04
    LR=0x7F4598

zero:
    0x7F4640
    0x7F4644 BL 0x8B2B70
    LR=0x7F4648

P77 proves the failing Tobi route does not reach the second path.

Exact virtual +0x1288 return during the failing attempt is still
NOT runtime-proven.

Do not patch it yet.


======================================================================
65. R78 NEXT ACTION — SEMANTIC ALT ROUTE PROBE
======================================================================

Next probe:

P78A

Safe normal function-entry target:

main+0x8B2D04

Exact caller return:

main+0x7F4598

ABI remains P75-proven:

uint32_t(void* actor)

P78A architecture:

Install P77A baseline first.

Add ALT helper trampoline.

Preserve:

ret = Orig(actor)
return ret

Log ALT calls only for semantic-enabled actor identity.

No char281 gameplay branch.

No gameplay write.

No global hot-loop cap.

Runtime test should be intentionally short:

Tobi player
wait until match active
perform ONE XXA attempt
stop soon after requested445.

Required evidence:

semantic=1
ALT helper at caller 0x7F4598
immediately around failing requested445

while P77 still shows no UJ helper call.

If this occurs:

the early branch before 0x7F4640 becomes PROVEN RUNTIME,
and the next target is the virtual+0x1288 policy source.

Do NOT force its result before proving its native semantics.



END MASTER CHECKPOINT R78
