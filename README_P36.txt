NSC2Switch P36 — STAGE / VICTIM LIFECYCLE TRACE

PURPOSE
P35A hardware result:
- custom Event236 dispatcher active;
- StageMove opcode 2 PASS;
- Tobi own Kamui still stalls after capture;
- Tobi awakening still unavailable;
- Tobi disappears after some enemy UJs, reported for Naruto slot 1 and Isshiki, but not Naruto Sage slot 5.

USER OBSERVATION TO TEST
The failing enemy UJs appear to use a different cinematic/stage lifecycle. P36 tests this directly instead of forcing visibility.

GAMEPLAY SEMANTICS
- Inherits P35A generic Event236 behavior unchanged.
- Vanilla charID <= 280 stays native.
- Custom charID > 280 uses the generic P35A dispatcher.
- No Tobi/281-specific route.
- No visibility/control force.
- No CPK/resource change.
- P33A Sorted=0 custom CPK remains required.

NEW READ-ONLY TRACE HOOKS
- main+0x8162D4 Event235 / ME_ENEMY_DISP_ON
- main+0x6E8EB0 HandleStageChange
- main+0x48E40C FixCharPosition
- main+0x48E61C PostStage

MARKERS
[NSC:P36] STAGE_HANDLE phase=0/1 stage=<id>
[NSC:P36] FIX_CHAR phase=0/1 actor=<ptr> valid=<0/1> side=<n> char=<id>
[NSC:P36] POST_STAGE phase=0/1
[NSC:P36] EVT235_SHOW actor=<ptr> side=<n> char=<id> ...
[NSC:P36] EVT236 ... text=<sanitized event string>
[NSC:P36] ACTION ... found=<0/1> index=<n>

Event236 logging is focused to avoid P35A's 768-entry spam. O14 is logged only for p3=0. Gameplay handling is unchanged.

DEPLOY AFTER CI BUILD
Keep P33A Tobi_Switch.cpk Sorted=0 and current RomFS/params/charicon.
Use the restore main included in the P36 CI artifact (baseline SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9).
Replace subsdk9 with the P36 compiled artifact.

TEST ORDER — IMPORTANT
Fresh boot. Reproduce the same contrast in one run if possible:
1. Tobi vs Naruto slot 1; let Naruto UJ hit; record whether Tobi disappears.
2. Tobi vs Naruto Sage slot 5; let UJ hit; record whether Tobi stays normal.
3. Tobi vs Isshiki; let UJ hit; record whether Tobi disappears.
4. Use Tobi StageMove once as a positive control.
5. Use Tobi Kamui UJ once.
6. Stop emulator and send the complete fresh log.

DECISION
- Failing UJ has STAGE_HANDLE/POST_STAGE and PASS UJ does not: user's stage-lifecycle hypothesis is strongly supported.
- FIX_CHAR after failing UJ uses a new custom actor pointer: actor recreation/pointer lifetime becomes primary target.
- Stage transition occurs but custom actor never reaches FIX_CHAR: missing custom victim stage-fix path.
- EVT235_SHOW is absent after failing UJ but present after PASS UJ: display restore path is missing.
- Same lifecycle sequence in PASS and FAIL: move one layer downstream into cinematic victim state/visibility ownership.

P36 IS A DIAGNOSTIC BUILD, NOT THE FINAL FIX.
