# NSC2Switch MASTER CHECKPOINT --- 2026-09-24 R90

## 0. Purpose / status

This checkpoint supersedes earlier working-state notes for the current
UltimateStormAPI / NSC2Switch Switch v1.70 investigation. It preserves
all locked constraints, negative experiments, P89 admission result, and
the new P90 static findings. Current unresolved frontier is NOT UJ
admission anymore; it is the cinematic / hit-confirm handoff after
native UJ admission and after action progression reaches 700 -\> 707 -\>
708.

## 1. Target / fingerprints

-   Game: Naruto x Boruto Ultimate Ninja Storm Connections, Nintendo
    Switch update v1.70.
-   Program ID: 0100FA10190A0000.
-   clean update main SHA256:
    01a0557acd4fd8ae54a2c13e4cc70de62cf32091dbfff40f407321bac312af44
-   Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
-   .text VA: 0
-   .text size: 0x12F5FD0.
-   canonical restore/vanilla main SHA256:
    2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
-   paired-main source-parity patch: main+0x7F2A9C, BD001FE0 -\>
    D503201F.
-   paired main SHA256:
    1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0.
-   exlaunch pinned commit: 229bbd6.

## 2. Non-negotiable architecture

Generic/data-driven solution only. Tobi custom ID281 is a fixture, never
a final hardcode. Never: - char==281 gameplay fix - donor 57-\>281
hardcode - force action700 - 445-\>700 rewrite - force E94=0x87 -
globally force F58 - selector1 -\> native selector8 - restore raw
Event236 - resurrect 0x7E1404 forced-tail patch - transplant PC
RVA/actor offsets blindly - delayed raw actor-pointer workers - manually
replay mid-function BLR from C++ and assume ABI parity. All gameplay
writes require static proof + runtime proof + native preservation +
generic policy.

## 3. Locked Event236 / victim-side result

Switch native event236 collides with MovesetPlus extension semantics.
Raw native Event236 must NOT be restored. P34A redirect diagnostic
proved the collision. P50 victim-safe/shadow infrastructure remains
required. Latest P89 runtime visual test: custom Tobi as victim of enemy
UJ is SAFE and does not disappear. Do not destabilize this path while
solving attacker-side cinematic handoff.

## 4. Locked action/state facts

Actor fields: - +E54 character ID - +E94 active action/state - +E98
previous - +E9C queued/requested - +EA0 related state/timer Native state
engine family: main+0x7A811C. Ordinary jutsu/custom XA: action445 /
E94=77. Vanilla UJ admission: action700 / E94=135. Observed custom UJ
after P89: native action700, then 707, then 708. Historical later UJ
states include 710, 711, 712, 713, 714, 740, but P90 must trace rather
than assume the exact complete progression.

## 5. Admission history --- solved

P58: 445/700 selection happens before PlayAction. P59: custom intended
UJ diverges before active action selection. P60 selector1-\>native
selector8 FAIL. P62 persistent selector8 FAIL
(chakra-charge/action148/repeated sound). P61 F58 forced true did not
solve. P66 manual mid-function BLR replacement broke vanilla UJ; never
repeat. P64F semantic producer works; original consumer path was wrong.
P85/R86: custom intended UJ had BDC8=1/F58=0/action445 while vanilla UJ
had BDC8=2/F58=1/action700. F58 direct gate at 0x7D3138 checks BDC8 \>=
2 around 0x7D3210..0x7D3218. P87 found active BDA4/BDC8 producer
override at 0x7D3AD0. P88B proved 0x8B30E4 can return true for BOTH
vanilla and custom at BDA4=3/BDC8=1, revising the earlier coarse P87
interpretation. Correct helper fields are actor+0x106F4, +0x123E0,
+0x123E4 (NOT 116F4/133E0/133E4).

P89A generic bridge: - whole-function trampoline at 0x7E24EC - preserve
native true - bridge false only when BDA4==3, BDC8==1, semantic UJ true,
and data-driven ougi/awakening membership true - no char281 hardcode -
no BDA4/BDC8/F58/action write. Runtime proved: - custom phase: native=0
semantic=1 member=1 bridge=1 out=1 - producer then natively advances
BDA4 3-\>4-\>5 and BDC8 1-\>2 - F58 becomes true - native requested700 /
PlayAction700 occurs - vanilla native=true remains preserved. Therefore
UJ admission/routing is SOLVED. Full cinematic is NOT solved.

## 6. Latest runtime frontier

Latest P89 visual/runtime test: - custom Kamui UJ admission succeeds -
action700 occurs - action707 occurs - action708 is observed - victim
becomes stuck in Kamui / cinematic handoff does not complete - custom
character as victim of enemy UJ remains safe. Current chain:
semantic/membership -\> P89 compatibility bridge -\> BDC8=2 -\> F58 true
-\> native 700 -\> 707 -\> 708 -\> STUCK before/inside
cinematic/hit-confirm handoff.

## 7. P90C static sweep validation

Input: canonical restore main. P90C_STREAM_SWEEP.txt: - SHA256 input
validated as canonical restore 2579... - NSO0 parsed successfully - text
memory offset 0 - text size 0x12F5FD0 - streaming Capstone sweep
completed - 251,426 output lines - 2,162 broad immediate hits (many are
false positives because immediate values can also be struct offsets;
only CFG-relevant hits count).

Known anchors decoded correctly: - 0x7E35E8 = BL 0x766B8C - 0x7D3138 =
F58 function - 0x7D3AD0 = active BDA4/BDC8 producer - 0x7E24EC = P89
actor predicate - 0x8B30E4 = UJ helper.

## 8. New P90 static finding A --- native action700 request

Function starts at 0x7E3534 and dispatches by W1. For W1==0 path: -
0x7E35D0 FMOV S0,#1.0 - 0x7E35D4 MOV W1,#0x2BC (700) - 0x7E35D8 MOV
W2,#-1 - 0x7E35DC MOV X0,X19 (actor) - 0x7E35E0 MOV W3,WZR - 0x7E35E4
MOV W4,WZR - 0x7E35E8 BL 0x766B8C - 0x7E35EC CBZ W0,0x7E387C. Thus
0x766B8C is a native action/request route used with action700, and its
boolean return gates continuation. P89 already gets custom through this
path at runtime.

## 9. New P90 static finding B --- extremely important 707/708 selector function

A strong post-admission function starts at 0x7E47B8 and dispatches on W1
0..4 through a jump table.

Key path: - 0x7E4810 MOV W20,#0x2C3 = 707 - call 0x768E84(actor,707,1) -
if non-null/success -\> retain 707 - otherwise: - 0x7E4828 MOV
W20,#0x2C4 = 708 - call 0x768E84(actor,708,1) - if that fails -\> branch
0x7E4BC8 - chosen W20 is then sent to: - 0x7E4840 FMOV S0,#1.0 -
0x7E4844 W2=-1 - X0=actor - W1=W20 (707 or 708) - W3/W4=0 - 0x7E4858 BL
0x766B8C. This is the first high-value P90 cinematic successor anchor:
it explicitly chooses 707 vs fallback 708 using 0x768E84, then requests
the selected action through the same 0x766B8C route family.

After request: - 0x7E485C..0x7E4864 calls 0x795F58(actor,1) -
0x7E4868..0x7E4874 calls 0x7932DC(actor, actor+0xB98C) -
character-specific branches follow at 0x7E4878 onward. These branches
must NOT be treated as a generic fix point.

## 10. New P90 static finding C --- active-state handling around 707/708

Another path beginning around 0x7E48B0: - calls 0x76B0C8 - calls
0x7C3D4C - calls 0x766A98(actor), then inspects returned current
action/state: - compare 0x2C5 (709) at 0x7E48C8 - compare 0x2C4 (708) at
0x7E48D0 - compare 0x2C3 (707) at 0x7E48D8. If current ==707: -
0x769A4C(actor) must be nonzero or branch to 0x7E4E24 - query
0x768E84(actor,708,1) - if query succeeds, invoke vfunc +0xF98 with
action708, -1, 0 and S0=1.0 at 0x7E4900..0x7E4920 - clear actor+0xEA4
pointer-sized field at 0x7E4924 - branch to 0x7E4E24. This is a much
stronger candidate for the 707-\>708 handoff than blindly tracing all
2,162 immediate hits.

If current ==708, control branches to 0x7E4B00. That block reads
actor+0xEA4 and timing globals, performs timing comparison, and branches
through additional conditions. Therefore actor+EA4 is now a
high-priority runtime snapshot field around 707/708.

## 11. New P90 static finding D --- fallback at 0x7E4BC8

If 707 and 708 action lookup/availability path fails earlier, 0x7E4BC8
requests action 0x4A (74) through 0x766B8C and then tail-calls a vfunc
+0xDF0. This is a failure/fallback branch, not something to force.

## 12. New P90 static finding E --- later action710 appears in separate handoff logic

Relevant hit: - 0x7E6C40 MOV W1,#0x2C6 (710) - W2 loads attacker/actor
char ID, W3 loads another actor/object char ID - 0x7E6C4C BL 0x76BDC0 -
returned value flows onward. 0x76BDC0 itself contains special mapping
logic for action710 under specific character combinations. This proves
raw immediate 710 hits can include action remapping policy, so P90 must
distinguish action transition from character-specific mapping. Do NOT
hook/override this globally without runtime proof.

Other later-state anchors from the sweep: - 710: 0x7E6C40, 0x7E6EA8,
0x7E7B8C, 0x7E8DAC - 711: 0x7E91D0 - 740: 0x7E9718 / 0x7E9730 -
712/713/714 also appear in 0x76BDxx mapping/comparison logic and many
unrelated struct-offset false positives. These are secondary until
runtime proves custom reaches their corridor.

## 13. P90A tracing design --- current plan

P90A must remain read-only and preserve P89 exactly.

Priority trace corridor: A. action request route 0x766B8C: - only log
calls when requested action is in
{700,707,708,709,710,711,712,713,714,740} OR actor currently in this UJ
corridor - actor snapshot before/after: E54/E60/E94/E98/E9C/EA0/EA4,
BDA4/BDC8 - return value and LR/caller offset.

B. 707/708 lookup/query route 0x768E84: - log callsite-specific calls
from 0x7E4820, 0x7E4838, 0x7E48F8 - arguments and returned
pointer/result - actor snapshot.

C. current-action getter 0x766A98: - trace callsite around 0x7E48C4 -
record returned action.

D. predicate 0x769A4C: - trace callsite around 0x7E48E4 and relevant
nearby branches - record return.

E. 708 transition vfunc +0xF98: - avoid unsafe generic vtable
replacement if prototype is uncertain. - Prefer a verified callsite
probe / surrounding whole-function trace at 0x7E47B8 if exlaunch hook
architecture can safely capture entry/exit without replacing arbitrary
BLR. - Never repeat P66-style manual BLR replay.

F. actor+EA4: - snapshot before 707 path, before/after 708 transition,
and at 708 timing block 0x7E4B00. - Do not write it.

G. attacker/victim: - once a safe opponent resolver is
statically/runtime verified, snapshot both sides. - do not use delayed
raw actor pointers. - victim-side P50/Event236 behavior must remain
untouched.

## 14. Expected P90A runtime matrix

Run at least: 1. vanilla character native UJ that connects and completes
cinematic. 2. custom Tobi fixture intended UJ/Kamui that connects and
gets stuck. Prefer same opponent and similar battle conditions.

Compare first divergence in: - 707 availability (0x768E84) - selected
action W20 707 vs 708 - 0x766B8C return - 0x766A98 current action -
0x769A4C predicate - 708 lookup result - EA4 timing/state - whether
transition leaves 708 toward later native cinematic states.

Goal: identify the FIRST native predicate/state difference after P89
admission. Do not patch later symptoms until that first divergence is
proven.

## 15. Build-kit standing rule

Every artifact called "build kit lengkap" MUST be P40-style drop-in: -
extract into repo root - files already in final paths - git add -A /
commit / push - CI builds without APPLY.py, sed, namespace repair,
source editing, or workflow debugging. Before release validate
source/header consistency, entrypoint, workflow, exlaunch pin,
paired/restore hashes, packaging paths, artifact name, marker presence
where applicable, manifest self-exclusion, and no stale workflow. If
this standard is not met, do NOT call it a complete build kit.

## 16. Current artifacts / evidence

-   P90C static sweep uploaded: P90C_STREAM_SWEEP.txt, 251,426 lines,
    \~8.86 MB.
-   Latest compiled P89 artifact historically:
    NSC-P89A-complete-dropin.zip, ZIP SHA
    d9ba0024eac5579b67a84c932bdb942be16ed0868c487bed25915c8e2debe07e.
-   active paired main SHA: 1adc4dfe...
-   restore main SHA: 2579b0...
-   latest runtime log before P90: uzuy_log(33).txt.
-   P89 admission is solved; cinematic handoff remains unresolved.

## 17. Immediate next action

Do NOT ask for another giant static dump. The P90C file already exposes
the key 707/708 corridor. Next engineering task is to build P90A from
the actual current P89 source baseline, using only safe/read-only probes
around the proven corridor above. If current P89 source tree is not
available as an attached/library source, retrieve it from Files/Library
or request the latest source zip; do not reconstruct source from the
compiled NSO artifact.

# R91 — P90A BUILD-KIT FREEZE

P90A source baseline is the actual P89A P40-style v3 source kit present in the working container. No source was reconstructed from subsdk9.

P90A active entrypoint: `InstallP90ACinematicHandoffTrace()`.

P90A preserves the complete P89 parent chain and adds exactly two new whole-function, preserve-Orig, read-only trampolines:

- `main+0x768E84` ActionLookup(actor,index,flag), logging only UJ-range 700..740 and capturing caller LR plus E60/E94/E98/E9C/EA0/EA4/BDA4/BDC8 before/after.
- `main+0x769A4C` ActionGate(actor), logging only relevant UJ corridor state / proven 0x7E48E8 caller and the same snapshots.

P90A deliberately does NOT double-hook `0x766B8C`; the inherited P50/P59 PlayAction trampoline already records native 700/707/708 progression. It also does not hook the large `0x7E47B8` dispatcher and does not replay its virtual `+0xF98` BLR. This is specifically to avoid repeating the P66/P88A ABI/boot-risk class.

P90A has no Event236/victim change, no BDA4/BDC8/EA4/action write, no F58 override, no force700/708, no selector8 mapping, and no char281 gameplay branch.

Source preflight PASS:
- P90 entrypoint/header/source consistency PASS.
- P89 parent/bridge retained PASS.
- lookup/gate offsets and markers PASS.
- EA4/caller snapshots PASS.
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0` PASS.
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9` PASS.
- exactly one workflow remains: `build-subsdk9-p90a.yml`.
- exlaunch remains pinned to `229bbd6` in CI.
- linked ELF marker checks require P90 READY/LOOKUP/GATE and inherited P89 READY/ACTOR_PRED before packaging.
- artifact manifest excludes `SHA256SUMS.txt` itself.

Important validation boundary: local source/static preflight is PASS. Actual devkitA64 compilation is intentionally performed by the included GitHub Actions workflow; do not claim runtime/compile PASS until that CI artifact exists and is audited.
