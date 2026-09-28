# NSC2Switch MASTER CHECKPOINT — 2026-09-27 R153 FULL
## V2I HARDWARE RESULT + V2J SWITCH-NATIVE STAGE / D-PAD CONSUMER PROBE

> **Purpose:** single recovery document for continuing the NSC2Switch project in a new chat/session/model.
> This checkpoint preserves the complete historical lineage below, while the recovery block at the top states the current verified frontier.
> Future work MUST update this document after every meaningful patch/test so the investigation never restarts from superseded hypotheses.

---


## R162 OVERRIDE — V2O HARDWARE RETIRED; V2P PASSIVE STAGEINFO/CPK ORDERING PROBE

Date: 2026-09-28

This section overrides the R161 V2O decision tree where they conflict. Preserve the full historical record below, but use this as the current frontier.

### New hardware input
- `uzuy_log(36).zip` SHA256 `d7d77151d4d90a6e816903ccde3b83f6c5131e71d4b4aeb84a8e4cffb251f903`.
- extracted `uzuy_log(36).txt`: 104,857,628 bytes, 886,618 lines, SHA256 `08529cf57601e1fda21daec6d452c789db8cfc2d1e3d42dbd63c21b50def7f20`.
- tested runtime artifact `NSC-RUNTIME-V2O-native-stage-reindex.zip` SHA256 `9ceeaaed3a976da2f34c32cbd884432c4f08030437332d8cca157220e459f659`.
- deployed `main` remains exact original v1.70 SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- source-side V2O verifier had passed all locked baseline checks before hardware test.

### V2O decisive hardware failure boundary
- V2O READY appears at 5.170347 s.
- custom extra CPK bind succeeds at 6.964640 s with priority 32 and bind_id 3.
- Tobi UJ admission/session remains functional before the failure.
- at 65.774596 s, V2N read-only lookup reports `STG_2TOB_UNI_LT`, key `0x01D1CA7E`, `found=0`.
- the next line at 65.774711 s is `Unmapped InvalidateNCE` for address `0x7640e41000`.
- after that registry miss there are zero further `[NSC:*]` markers in the log.
- there are zero `[NSC:V2O] STAGE_REINDEX` markers.
- total `Unmapped InvalidateNCE` rows: 884,191.

Therefore V2O did **not** produce `after_found=0` or `after_found=1`. Execution did not return through the planned post-loader path. The direct mid-battle call to `main+0x835FAC(stage_manager)` is RETIRED. Do not run the same V2O experiment again.

### Static correction
Original v1.70 main has one native BL caller to `main+0x835FAC`, from the StageInfo initialization chain at `main+0x406498`. This proves that `0x835FAC` is a native StageInfo initializer/loader and that the +0x148 manager identity is correct. It does **not** prove the whole initializer is safe to re-enter from Event236 after the manager is already live. Native duplicate-key handling inside the insertion path is insufficient evidence of whole-loader reentrancy.

### V2P design — passive ordering proof only
V2P must contain NO direct `main+0x835FAC` call and NO new StageInfo trampoline. Reuse the already-proven `FileLoadRequestHook` from the V2M baseline to observe the game's natural requests for:
- `data/stage/StageInfo.bin.xfbin`
- `data/stage/AdvStageInfo.bin.xfbin`

At natural request pre/post, log whether `Tobi_Switch.cpk` has already bound successfully. At successful extra CPK bind, log whether a StageInfo request was already seen. Keep V2N's Event236 registry lookup unchanged.

Required V2P markers:
- `[NSC:V2P] READY passive_stageinfo_order_probe=1 ... new_trampoline=0 native_loader_call=0 ...`
- `[NSC:V2P] STAGEINFO_LOAD_REQ phase=pre ... cpk_bound=0/1 ...`
- `[NSC:V2P] STAGEINFO_LOAD_REQ phase=post ... cpk_bound=0/1 ...`
- `[NSC:V2P] CPK_BOUND ... stageinfo_seen_before_bind=0/1 ...`
- existing `[NSC:V2N] STAGE_REGISTRY ... STG_2TOB_UNI_LT ... found=0/1`

Decision tree:
1. natural StageInfo request with `cpk_bound=0` and later `stageinfo_seen_before_bind=1` => registration ingestion happens before custom CPK availability; fix load/bind ordering or provide pre-init merged StageInfo.
2. natural StageInfo request with `cpk_bound=1`, but later V2N custom key remains `found=0` => CPK is present during ingestion; fix StageInfo compiler/packaging/semantic merge PC-side.
3. natural StageInfo request with `cpk_bound=1` and later custom key `found=1` => registration works; continue downstream into descriptor/environment setup.
4. no natural StageInfo marker => do not infer ordering or packaging; trace the lower-level ingestion boundary read-only.

### Locked priority after R162
1. Build/test V2P passive StageInfo/CPK ordering probe.
2. If ordering bug: fix custom CPK/merged StageInfo availability before native initialization.
3. If packaging bug: audit compiler output and merged `data/stage/StageInfo.bin.xfbin` semantics.
4. Only after custom registry `found=1`, return to environment/resource lifecycle.
5. Event150 Tobi voice afterward.
6. D-pad/Izanagi last.

Locked exclusions remain unchanged: do not reopen P128/raw15/session; no manual descriptor/tree insertion; no manual PostStage; no char281 gameplay branch; no global visibility/damage override; opcode26 generic audio remains frozen PASS.

---

## 0. RECOVERY INSTRUCTIONS FOR THE NEXT AI / NEXT SESSION

Read this file first before proposing any new patch.

Do **not** restart from V2E/V2F/V2G hypotheses. Current highest verified state:

- Target remains Storm Connections Switch v1.70, Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`.
- Original-main V2D architecture is still locked: original main on disk, resolver 7/7, validate-before-write exact 30-word runtime patch, P128 UJ corridor/session path preserved.
- Latest hardware-tested build is **V2I**, user artifact `NSC-RUNTIME-V2I-activation-core-stage-audio-parity.zip`.
- V2I deployment is verified: original main SHA `2579...ecd9`, V2I subsdk9 SHA `5a034a499702892e446e289b2ff5a40abd85fbb68ce23d9b05d8e712f5462bbc`.
- **Opcode26 generic audio is hardware PASS.** Runtime calls actor vtable+0x1030 for known UJ cues and user confirms Tobi UJ now has audible sound. Freeze this path unless a specific missing cue is later reported.
- **UJ stage lookup/state-ID is PASS but visual environment is still FAIL.** `STG_2TOB_UNI_LT` resolves to CRC `0x01D1CA7E`, live stage ID becomes `0x01D1CA7E`, yet the battle map remains visibly mixed with the Kamui stage.
- V2I stage path fixed actor + enemy but deliberately omitted Switch `main+0x48E61C`. Static original-main proof now shows native Switch transition sequence `HandleStageChange -> FixCharPosition(actor) -> 0x48E61C`. V2J tests the combined PC+Switch requirements: fix actor + enemy, then execute the native post-stage/member sweep.
- **Right D-pad visibility remains safe** because PL_ANM930 is still suppressed. V2I applies exact source activation core `SW_MTOB_XH` + Right charge `100.0f`, but user reports this appears to affect the D-pad/substitution cells only, not full advertised Izanagi protection.
- Do not interpret V2I as full Izanagi. Do not add a global no-damage flag. Source PL_ANM930 contains temporary DMGHIT/BODHIT off/on events, so persistent minute-long protection must be recovered through the intended native condition/D-pad machinery.
- PC source uses actor+`0xF30` as D-pad-animation enable. Switch original main independently contains an F30 consumer at `main+0x7E74A4` inside the resolved STATE137 controller family, followed by actor virtual +0xBA8 and +0xBB8. V2J adds one read-only exact-instruction replay probe there.
- Opcode17 remains source-parity and solved. Do not reopen the old abs<=16 theory.
- V2G full PL_ANM930 route remains rejected as a final opcode23 implementation because it reproduces Tobi disappearance. V2I/V2J keep the safe suppression.
- UJ admission/root remains solved. Do not reopen raw15/P128, force708/710, or bypass native session setup.
- Victim-UJ safety remains locked. Do not globally force visibility.
- No final char281 gameplay branch. char281 is fixture only.
- `subsdk9` remains bootstrap until feature parity is complete.
- **V2J source is prepared and source-verified.** Package: `NSC2Switch_RUNTIME_V2J_STAGE_NATIVE_POST_DPAD_CONSUMER_PROBE_DROPIN.zip`, SHA256 `a10e72627497631f078a31fb2c054b4b9cdf8ed6fd830cb20220e896fb1b754d`.

Next hardware test should be exactly:
1. fresh boot;
2. Right D-pad once, observe cells and then let enemy hit/jutsu Tobi;
3. Tobi own UJ once, observe whether Kamui still mixes with battle map;
4. save full log immediately.

Required V2J markers:
- `[NSC:V2J] DPAD_NATIVE_READY ... installed=1 ...`
- any `[NSC:V2J] DPAD_NATIVE_CONSUMER ...` around/after Right activation;
- `[NSC:V2J] STAGE2_SWITCH_NATIVE ... poststage=1 ...` for Kamui and restore stage;
- existing `[NSC:V2I] OP26_PLAY ...` should remain as audio regression proof.

When a new artifact/log is supplied:
1. hash artifact/log and verify exact deployed original main + subsdk9;
2. verify resolver 7/7 and runtime 30-word patch first;
3. inspect V2J D-pad consumer markers and stage marker;
4. do not mutate gameplay until the probe identifies the next native boundary;
5. update this checkpoint before ending the iteration.

---

# 1. PROJECT IDENTITY / ENVIRONMENT

Game:
- **NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS**
- Platform target: Nintendo Switch
- Update target: **v1.70**

Program ID:
- `0100FA10190A0000`

Main Build ID:
- `48ece454b61412b9fb46fab2be3f5ef7b2804f39`

exlaunch pin:
- `229bbd6`

Primary user environment:
- Android / Termux
- Ubuntu-in-Termux occasionally
- GitHub Actions + devkitA64 for builds
- Uzuy emulator for runtime tests

Original/restore v1.70 main SHA256:
- `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

Historical baseline main SHA256 used before V2D:
- `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`

Historical P128 paired patched-main SHA256:
- `904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff`

Latest hardware-tested V2I user artifact:
- file: `NSC-RUNTIME-V2I-activation-core-stage-audio-parity.zip`
- ZIP SHA256: `b4b429cda99d15e981fc3713a233fd485c71e36b42e1d1c398f15a5ae2115db0`
- deployed `main` SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- deployed `subsdk9` SHA256: `5a034a499702892e446e289b2ff5a40abd85fbb68ce23d9b05d8e712f5462bbc`
- restore `main` SHA256: original hash above
- hardware verdict: **audio PASS; stage ID changes correctly but visual battle-map mixture remains; Right core changes cells/charge but is not full Izanagi.**

Latest user runtime log:
- file: `uzuy_log(31).txt`
- SHA256: `38a6586c5e095c016ade1b8bd3ddde85df1870930c139f1cdbd5c757e56d31c0`
- line count: 12064

Latest prepared source-only V2J package:
- file: `NSC2Switch_RUNTIME_V2J_STAGE_NATIVE_POST_DPAD_CONSUMER_PROBE_DROPIN.zip`
- ZIP SHA256: `a10e72627497631f078a31fb2c054b4b9cdf8ed6fd830cb20220e896fb1b754d`
- verifier marker: `NSC_RUNTIME_V2J_SOURCE_VERIFY=PASS`
- workflow artifact name: `NSC-RUNTIME-V2J-stage-native-post-dpad-consumer-probe`
- stage: fixes actor + enemy and restores Switch-native post-stage sweep `main+0x48E61C`;
- D-pad: one read-only resolver-derived probe at native F30 consumer `main+0x7E74A4`;
- audio: V2I opcode26 path unchanged/frozen.

---

# 2. MOD / CHARACTER CONTEXT

Initial mod set:
- Isshiki Moveset v1.2.1 (`.nsc`)
- Tobi / Madara (`.unse`)
- Yahiko (`.uns`)
- Toneri (`.nsc`)

Current main fixture:
- Custom Tobi generated char ID **281**
- Donor used historically for SpecialCond analysis: Danzo ID **57**
- Native condition family: `COND_2DNZ`

Important policy:
- **ID281 is not allowed as a final special-case branch.**
- Final behavior must be generic/data-driven.
- Do not globally alias every custom char to donor57.
- Donor57 is a reverse-engineering clue only.

---

# 3. ORIGINAL TOBI SYMPTOMS

Historical Tobi failures:
- enemy disappeared / low-poly / HUD issues around awakening;
- some opponents became unhittable;
- Tobi own UJ Kamui failed to enter cinematic;
- if Tobi was victim of enemy UJ, battle could continue but Tobi became invisible/unplayable;
- Tobi awakening unavailable/broken.

These were separate bugs, not one single issue.

---

# 4. MASTER INVARIANTS / DO-NOT-REGRESS RULES

These are locked rules from the investigation:

1. **Natural action708 is legitimate.**
   - Do not suppress 708.
   - Do not globally redirect 708.
   - Do not force action710 as the final solution.

2. Do not force state137 globally.
   - P107 proved that jumping to137 can start cinematic but skips native lifecycle setup.

3. Do not directly create/force cinematic sessions as the final fix.
   - Native session setup through `0x7EF098` must remain authoritative.

4. Do not globally mutate custom SPL damage types.
   - Custom Tobi damage records:
     - idx1847 `DMG_MTOB_SPL00`
     - idx1848 `DMG_MTOB_SPL01`
   - final count1849.

5. Preserve victim-safe Event236 compatibility:
   - visibility shadow
   - control shadow
   - known custom-event compatibility behavior

6. Preserve P89 generic semantic/membership UJ admission.

7. No final char281 branch.

8. Resolver behavior must be **fail-closed**:
   - zero hits => do not patch/hook;
   - multiple hits => do not patch/hook;
   - never silently use an old hardcoded offset as fallback.

9. Current V2 architecture is **update-resilient**, not guaranteed update-proof.
   - If code shifts but signatures survive, resolver can continue automatically.
   - If Bandai changes function structure/semantics, a signature/validator may need maintenance.

---

# 5. EARLY BUILD / BASELINE HISTORY

Important earlier build checkpoints:
- Alpha11
- Alpha14b = functional baseline / PASS
- Alpha14c = audit branch

Older A/B notes:
- V20D: enemy not hittable
- V25: PASS
- V27A: FAIL
- V33A: PASS

Early hook experiments included:
- `0x7E13E4`
- `0x7E1404`

Early P3–P4A still failed Tobi-as-UJ-victim behavior.

R66 extracted / identified:
- `OugiFinishParam.bin.xfbin`
- `finalSpSkillCutIn.bin.xfbin`
- `ultimateJutsuParam.bin.xfbin`
- `conditionprm.bin.xfbin`

Relevant archives:
- patch/170/common.cpk
- base data2.cpk

---

# 6. SPECIALCOND / DONOR57 AUDIT

Eight native charID57 / `COND_2DNZ` consumers were identified:
- `0x778B2C`
- `0x7EAFEC`
- `0x7EB048`
- `0x7EB0B0`
- `0x7EB144`
- `0x7EE8B0`
- `0x7F537C`
- `0x7F56B8`

Alpha14c local Tobi281->57 mapping was tested.

Result:
- some related behavior improved;
- own UJ still failed;
- therefore SpecialCond alias alone was insufficient.

Conclusion:
- do not solve Tobi by permanent 281→57 hardcoding.

---

# 7. EVENT236 ROOT-CAUSE HISTORY

Native Switch Event236 semantics conflicted with MovesetPlus semantics.

Key discovery:
- native Event236 interpreted the custom opcode stream incorrectly, causing visibility/control corruption.

P34A:
- no-op experiment proved native Event236 handling was responsible for disappearance/hitability/victim-UJ corruption.

P35+:
- generic dispatcher architecture.

P37/P38:
- visibility/control shadow logic.

P50:
- victim-safe Event236 baseline.
- critical compatibility state from P50 remains part of the functional baseline.

Current P50-style functionality includes custom event handling plus shadow compatibility.

PC MovesetPlus source dispatch body establishes:
- opcode12 = set player visibility
- opcode13 = enable D-pad animation
- opcode14 = enable control
- opcode15 = disable control
- opcode16 = timed control
- opcode17 = change D-pad charge
- opcode18 = gray effect
- opcode19 = HUD control
- opcode20 = IA
- opcode21 = camera algorithm
- opcode22 = play PL animation
- opcode23 = `me_play_action`
- opcode24 = face animation
- opcode25 = timed face animation
- opcode26 = `me_play_voice_string`
- opcode27 = projectile deflection ON
- opcode28 = projectile deflection OFF
- opcode29 = take over enemy projectiles

This exact PC source mapping must be treated as the semantic reference when porting missing custom events.

---

# 8. DPAD EXACT PC SOURCE FACTS

PC source:
`me_change_dpad_charge(char_p, enemy, arrow, charge)`

For PC v1.70:
- D-pad charge base offset = `0x12B88`
- Up = +0
- Down = +4
- Left = +8
- Right = +12
- arrow0 updates all four.

PC source:
`me_enable_dpad_animation(a1, param2)`

For PC v1.70:
- writes `param2` to `a1 + 0xF30`.

These PC offsets are **not assumed valid on Switch**; they are semantic evidence only.

---

# 9. P89 GENERIC UJ ADMISSION

P89 established generic semantic/membership admission for custom UJ behavior.

This remains a required baseline.

Do not replace it with a Tobi-only ID check.

---

# 10. UJ ACTION GRAPH — LOCKED FACTS

Custom Tobi intended/natural action graph:
- 700
- 707
- 708

Action708 is legitimate.

P96 custom action707 descriptor:
- `d6c=0`
- `d72=2`
- `d94=80`
- key707=`PL_ANM_SPSKILL_1_LOOP`

Natural selector calls PlayAction708 from caller:
- `0x7725D0`

P97 suppression of 707→708 failed and is retired.

---

# 11. UJ SESSION / CINEMATIC INVESTIGATION

## P107 — useful positive control, but retired as final solution

P107 bridged cleanup125→137.

Positive result:
- custom action708 reached native PlayAction710 from `0x7E6EC8`;
- cinematic began.

But lifecycle was incomplete:
- UJ voice/audio missing;
- Kamui stage mixed with normal battle stage;
- enemy disappeared;
- Tobi uncontrollable afterward;
- no proper continuation.

At P107 state137, context was stale:
- `E98=63`
- `BDA4=1`

Conclusion:
- state137/controller/710 machinery is viable;
- direct cleanup125→137 skips required native setup;
- P107 endpoint is evidence only, not final behavior.

## P108
cleanup125→136 caused replay:
- 708→136→707
Retired.

## P109 / P110
- vanilla request137 caller return = `0x74FF7C`
- successful vanilla manager phase3 resolves leader, requests state137, paired state81
- failing Tobi own-UJ had zero type10 manager invocation.

## P111 / P112B
P111 saw a victim125→126/action12 route in one successful vanilla matchup.

P112B corrected this:
- another successful vanilla UJ reached710 without that route.
Therefore victim125/126 is not a universal prerequisite.

## P113
Successful vanilla:
- native outer cinematic/session setup `0x7EF098`
- caller return `0x77C5EC`
- native return=1
- session9 `0→1`
- session10 `0→1`

Failing Tobi:
- zero P113 session rows.

Therefore failing custom Tobi did not even call `0x7EF098`.

## P114
type9 preflight call:
- `0x77C4B0 -> 0x750860`

Successful vanilla:
- focused type9 ret=0.

Failing custom:
- no focused type9 preflight.

Therefore type9 was not the initial custom blocker.

---

# 12. STATIC UJ CORRIDOR

Native corridor before session setup:

- `0x77C474` `LDR W8,[X20,#0x50]`
- normalized type `(raw & ~1)` must equal10
- reject at `0x77C480`

Then:
- actor C48 check around `0x77C490`
- actor reject `0x77C494`
- peer C48 check around `0x77C4A4`
- peer reject `0x77C4A8`
- type9 query `0x77C4B0`
- downstream pairing/lookup
- native `0x77C5E8 -> 0x7EF098`
- return at `0x77C5EC`

Important:
X19 / actor `[+0xB9E4]` in this dispatcher represents the **victim**, not the attacker.

---

# 13. DAMAGE CLASSIFICATION DISCOVERY

P118:
- victim cursor coherence proven.

P119:
successful vanilla:
- victim cursor126
- raw type10
- `DAMAGE_ID_SPATK_BEGIN_DIRECT`

Custom Tobi:
- idx1848 raw15
- then idx1847 raw24
- then natural708

This was the first proven UJ divergence.

---

# 14. P120 → P128 UJ FIX LINEAGE

## P120A
One narrow inline gate overlay:
- under appended custom damage + semantic action707 context
- raw15 converted to10
- no game-memory writes
- no forced action/session

Runtime:
- idx1848 raw15→10
- second idx1847 raw24 unchanged

Opened the real type gate but cinematic still did not occur.

## P121A
Attempted extra inline C48 hook.
Boot failed from trampoline exhaustion:
`AllocForTrampoline(...)`
Retired.

## P121B
Static NOP actor/peer reject experiment variant.

## P122A
Both C48 reject branches NOP.
Cinematic still did not occur.
Important historical warning:
- C48 rejection alone was not the final blocker.

## P123A
Tried downstream call-replay wrappers.
Caused regressions / freezes, including vanilla.
Retired.
Reason:
- wrapping native BL/BLR calls changed LR/caller provenance.

## P124A
Native-safe corridor reach probes.
Native calls remained untouched.

## P125A
P107-guided session-qualified state137 fallback:
- post-outer hook
- only arm after real native session setup
- cleanup125→137 only if session latch and mature context

P125 result:
- actor C48 appeared to be the next frontier,
- but later marker assumptions were refined.

## P126A
Static actor C48 reject bypass only.
No final cinematic.

## P127A
Full native-corridor A/B:
- actor reject open
- peer reject open
- type9 branch forced to success path
- lookup branch forced to null/success path
- native calls still called exactly once from main

Naruto/victim safety preserved but Tobi still stuck.
This exposed that prior marker logic was too strict.

## P128A — decisive UJ admission success

P128 moved the type gate into a static precise gate cave.

Policy:
- raw10/11 => native pass
- raw15 => pass only for narrow custom semantic action707 context
- raw24 => reject
- other => reject

Downstream P127 branch openings remained for the proof.

Result:
- Tobi own UJ enters cinematic.
- Tobi can move after UJ.
- Naruto UJ safe.
- Tobi victim-UJ safe.
- core cinematic session works.

P128 became the first fully useful functional UJ checkpoint.

Residual P128 issues:
- cinematic stage still mixes with battle map;
- audio/voice incomplete.

---

# 15. TOBI VOICE / AUDIO AUDIT — R145

Tobi is **not authored as a silent character**.

Event150 / voice-like named cues include:

Victory:
- `PL_ANM_WIN_S`, frame1 -> `mtob_win00`

Skill/cutin:
- `2tob_121`

Other special:
- `2tob_123`
- `2tob_124`
- `2tob_125`
- `3mdr_ougi_hit_002`

Tobi UJ dedicated cues:
- frame44  -> `mtob_ougi_001`
- frame114 -> `mtob_ougi_002`
- frame166 -> `mtob_ougi_003`

Same three occur in both:
- `PL_ANM_SPSKILL_1_DEMO_ATK`
- `PL_ANM_SPSKILL_1A_DEMO_ATK`

Event236 opcode26 sound cues in Tobi UJ:
- frame0   -> `S_PL_etc_l`
- frame69  -> `S_PL_DMG_cmn_vS_rv`
- frame209 -> `S_PL_etc_m`

Current compatibility gap:
- custom Event236 opcode26 is not fully ported;
- custom character sound-entry / ACB registration was historically not ported;
- therefore silence is a runtime parity problem, not evidence that the mod lacks voice.

Recommended audio work:
1. port/trace event150 custom voice lookup;
2. port Character Sound Entries;
3. port Character Sound ACBs;
4. port opcode26 `me_play_voice_string`;
5. confirm bank/cue presence;
6. then test win/skill/UJ voice.

---

# 16. CURRENT TOBI CONDITIONS / GENERATED CONDITION REGISTRY

Generated custom conditions currently observed:
- 512 `SW_MTOB_XH`
- 513 `SW_MTOB_ST`
- 514 `YXNQ_MTOB`
- 515 `SW_MTOB_BREAK`
- 516 `WC_MTOB_BREAK`

Native condition count:
- 512

Generated extra:
- 5

Total:
- 517

These are part of the runtime condition-count patch set.

---

# 17. DPAD-RIGHT CURRENT BUG

User-confirmed intended behavior:
- D-pad Right should show a Sharingan logo/effect;
- Tobi should remain visible;
- Tobi should become resistant/invulnerable to damage.

Current V2D behavior:
- D-pad Right still makes Tobi disappear.

Latest runtime evidence:
- Tobi reaches action928.
- Event236 opcode23 fires:
  - `text=SPTYPE_ACTION10`
  - `p3=77`
- custom dispatcher resolves `SPTYPE_ACTION10`
- found action index930
- PlayAction transitions `928 -> 930`

Therefore:
- input routing is not simply dead;
- action chain is executing;
- the remaining problem is semantic parity inside/around the SPTYPE action sequence (visibility / invulnerability / special visual handling), not inability to find the action.

Relevant source parity:
- opcode23 on PC = `MovesetPlus::me_play_action`
- D-pad feature also depends on PC opcode13/17 semantics and possibly other events in the SPTYPE action records.

Next D-pad analysis should inspect the full event sequence of:
- `PL_ANM_SPTYPE_ACTION08`
- `PL_ANM_SPTYPE_ACTION09`
- `PL_ANM_SPTYPE_ACTION10`
and identify which exact event produces:
- visibility change,
- Sharingan visual/logo,
- damage immunity / reaction suppression,
- state cleanup.

Do not “fix” disappearance by globally forcing visibility without first identifying the intended paired semantics.

---

# 18. CURRENT UJ STAGE BUG

Core UJ session is now functional.

Remaining visual issue:
- Kamui cinematic still contains/overlays normal battle-map geometry.

This is no longer an UJ admission problem.

Likely work domain:
- stage/environment cinematic transition,
- map/environment switch event,
- Tobi-specific `SW_MTOB_XH`,
- cinematic stage ownership/lifecycle.

Do not reopen raw15/session/cinematic admission unless new evidence directly contradicts V2D.

---

# 19. AWAKENING

Awakening was an original unresolved Tobi symptom.

PC source contains explicit Ougi/Awakening compatibility code for PC versions, including “ultimate jutsu in awakening” behavior.

Switch awakening parity is not yet considered complete.

Keep awakening as a separate feature subsystem after:
1. D-pad parity,
2. audio parity,
3. UJ stage parity.

---

# 20. RUNTIME V2 ARCHITECTURE

The project pivoted from v1.70 absolute offsets toward an update-resilient runtime.

## V2A — read-only resolver coexistence proof

Resolved 7 anchors uniquely:
- CHARACODE_GETTER
- CPK_BIND
- EVENT236
- PLAY_ACTION
- CENTRAL_SETTER
- UJ_SESSION_OUTER
- STATE137_CONTROLLER

Hardware result:
- 7/7 PASS.

P128 still provided gameplay safety.

## V2B — first functional dynamic hook migration

Moved hook installation to resolver results for:
- EVENT236
- PLAY_ACTION
- CENTRAL_SETTER

Rules:
- resolver-only
- fail-closed
- no offset fallback

Hardware result:
- PASS.

## V2C — dynamic core migration

Additionally migrated:
- CPK_BIND
- CHARACODE_GETTER
- UJ_SESSION_POST derived from UJ_SESSION_OUTER

P77 diagnostic trampoline was reclaimed to stay within trampoline budget.

Hardware result:
- CPK bind executed successfully.
- char281 resolved to `mtob`.
- Tobi UJ session remained functional.

## V2D — ORIGINAL MAIN / RUNTIME PATCH PROOF

Highest verified runtime architecture as of this checkpoint.

Deployed file `main` is original/restore v1.70.

V2D:
1. resolves the 7 anchor functions;
2. derives `UJ_SESSION_POST`;
3. resolves the UJ gate locally;
4. resolves five condition-count patch sites;
5. resolves the P67 prerequisite;
6. validates the entire patch plan first;
7. applies the exact proven 30-word main delta in runtime memory;
8. installs dynamic hooks.

Runtime patch delta:
- 5 condition-count words
- 1 P67 prerequisite
- 24 P128 UJ corridor words
- total 30 words

No runtime write happens until all required sites are uniquely resolved and original fingerprints match.

V2D is **not yet the final zero-hardcode release**:
- older P50/P67/P81 compatibility internals still contain v1.70-specific sites that must later be migrated;
- `subsdk9` is still the bootstrap loader.

---

# 21. LATEST V2E HARDWARE EVIDENCE

Latest log:
- `uzuy_log(27)(1).txt`
- SHA256: `87644f135f9cd052dea204f417659365f83129b9bc150d7000ad215ec197f139`

Boot / architecture evidence:
- resolver ready 7/7, all seven anchors exact for v1.70;
- `fail_closed=1`, `no_offset_fallback=1`;
- original_main=1; paired_main_file=0;
- runtime patch ready with exactly 30 words (5 condition + 1 P67 + 24 P128);
- P50 READY reports `op17_source_parity=1`;
- P128 READY reports original main + precise gate cave.

UJ regression evidence in the same log:
- P128 `POST_OUTER` appears twice for custom Tobi with `ret=1 session_latch=1 raw=15`;
- no NSC resolver/patch/fingerprint failure markers are present.

D-pad exact evidence:
- custom Tobi reaches action928;
- opcode23 fires once with `p2=0 p3=77 text=SPTYPE_ACTION10`;
- PL_ANM resolver finds index930;
- current port performs the immediate-action write (E94 becomes77) and then calls PlayAction930;
- central setter proves current action `928 -> 930` while E94 stays77;
- action930 remains active for several seconds before a later normal transition;
- condition `SW_MTOB_XH` executes while action930 is live;
- opcode17 later fires with `p2=0 p3=4 p4=100.0`;
- V2E marker proves fourth D-pad field becomes `42c80000`;
- user observation: Tobi still disappears.

Visibility evidence:
- 33 Tobi `VIS_SHADOW` rows exist in this log; all 33 are `p2=1`;
- no Tobi `VIS_SHADOW p2=0` is present;
- therefore the recorded disappearance cannot be explained by the compatibility handler receiving an explicit opcode12 hide request in this run.

Log termination note:
- the only late Critical assertion occurs after emulation termination/config shutdown activity and is followed by frontend reinitialization; no `[NSC:*]` fatal/resolver/patch/fingerprint failure accompanies it. Treat it as emulator shutdown evidence unless a future run reproduces it during gameplay.

# 22. CURRENT FUNCTIONAL MATRIX

### PASS / currently safe
- Game boot under V2D
- Original/restore main on disk
- Dynamic resolver 7/7
- Runtime 30-word patch application
- Custom CPK mount
- Custom characode ID281 -> `mtob`
- P50 victim-safe behavior
- Naruto own UJ
- Tobi as enemy-UJ victim
- Tobi own UJ cinematic admission
- Tobi control after own UJ
- other Tobi jutsu after own UJ (user-tested)
- natural action708 preserved
- natural/native action710 route used

### PARTIAL / unresolved
- Tobi UJ environment/stage replacement
- Tobi UJ voice/audio
- Tobi general battle/skill voice parity
- D-pad Right Sharingan/invulnerability
- Tobi awakening parity

### RETIRED / do not repeat blindly
- suppressing action708
- forced710
- global forced137
- direct session creation
- P123 BL/BLR call-replay wrappers
- permanent 281→57 specialCond alias
- global custom SPL type mutation
- stacked new inline hooks that exceed trampoline budget

---

# 23. UPDATE-RESILIENCE STATUS

Current architecture is substantially closer to a PC-style ModdingAPI.

What is already reusable:
- RuntimeResolver
- CPK hook
- characode hook
- Event236 hook
- PlayAction hook
- central setter hook
- UJ session anchor
- dynamic/derived UJ gate/post
- runtime main patcher with validation

What this means for future game updates:

If an update only relocates code and signatures remain structurally compatible:
- resolver can find the moved functions automatically;
- no new patched `main` file should be needed.

If a function implementation changes substantially:
- the relevant signature/validator may fail;
- the runtime must fail closed;
- only that subsystem should need resolver maintenance.

Do not claim “100% immune to updates.”
Correct description:
- **update-resilient / self-resolving where signatures remain valid.**

---

# 24. WHY FUTURE MODDINGAPI PORTS SHOULD GET EASIER

We now have reusable runtime services instead of solving every mod from zero.

Target architecture:

`NSC2Switch Runtime`
- RuntimeResolver
- RuntimePatcher
- CharacterRegistry
- ConditionRegistry
- CpkManager
- ActionManager
- EventManager
- UjManager
- SoundManager
- AwakeningManager

Once one subsystem is correctly ported, future characters should reuse it.

Examples:
- opcode26 voice fix should benefit all custom movesets that use the same event;
- ACB registration fix should benefit later custom characters;
- UJ admission/session framework should benefit other custom UJs;
- condition expansion should benefit other generated conditions.

---

# 25. NEXT WORK ORDER — LOCKED PRIORITY

Do not remove `subsdk9` yet.

Recommended sequence:

## Priority 1 — D-pad Right parity
Goal:
- Sharingan indicator/logo appears
- Tobi stays visible
- damage immunity works
- feature exits cleanly

Use latest V2D.
Trace:
- input -> SPTYPE action
- action928 -> Event236 op23 -> `SPTYPE_ACTION10` -> action930
- full Event236 stream inside actions 928/930
- visibility and control state
- condition state (`SW_MTOB_XH`, `SW_MTOB_ST`, BREAK conditions)
- damage/reaction behavior

Port missing semantics generically.

## Priority 2 — Audio / voice full port
Port:
- event150 voice-like path
- Character Sound Entries
- Character Sound ACBs
- opcode26 `me_play_voice_string`

Validate:
- normal battle voice
- skill voice
- win voice
- UJ `mtob_ougi_001/002/003`

## Priority 3 — UJ environment/stage parity
Fix Kamui cinematic battle-map mixture.

## Priority 4 — Awakening parity
Treat separately from UJ admission.

## Priority 5 — Generic regression with added mod characters
Add more custom characters and ensure no Tobi-specific assumptions.

## Priority 6 — bootstrap migration
Only after gameplay parity is healthy:
- remove `subsdk9`
- move V2 runtime to external plugin/injection loader
- keep main original
- keep signatures fail-closed

---

# 26. TEST DISCIPLINE FOR FUTURE BUILDS

Minimum regression order after any runtime/core change:

1. fresh boot
2. verify resolver counts / no ambiguity
3. verify runtime patch validation/install
4. character select / hover Tobi
5. Naruto own UJ
6. Tobi as victim of enemy UJ
7. Tobi own UJ
8. move Tobi after UJ
9. test normal jutsu after UJ
10. test D-pad Right
11. test awakening if relevant
12. save full log before changing build

For audio builds additionally:
- normal hit/damage
- normal jutsu voice
- win voice
- Tobi UJ voice sequence

---

# 27. ARTIFACT / BUILD HYGIENE

For every new patch:
- preserve a versioned source ZIP;
- preserve compiled artifact;
- compute ZIP SHA256;
- compute deployed `main` SHA256;
- compute `subsdk9` or external-loader SHA256;
- record exact workflow name;
- only current workflow should be push-enabled;
- verify source after extracting the ZIP;
- compare runtime markers to expected markers;
- never mix an old `main` with a newer runtime.

For V2D specifically:
- active main must equal original/restore hash:
  `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

---

# 28. TRAMPOLINE BUDGET

Known hard runtime constraint:
- too many new inline/whole-function hooks can fail allocation.

P115A / P121A history proves trampoline exhaustion is real.

Therefore:
- prefer resolver + existing hook reuse;
- prefer static/runtime instruction patch when safe;
- reclaim diagnostic hooks when no longer necessary;
- avoid stacking read-only probes indefinitely.

---

# 29. IMPORTANT BINARY / OFFSET NOTE

Historical uncompressed NSO mapping used:
- text file offset = text file start (`0x101`) + main text offset

This was used to verify static patch locations.

Do not assume this mapping blindly for a different game version/container layout; validate the NSO structure first.

---

# 30. CURRENT LIBRARY / EVIDENCE FILES TO SEARCH FIRST

Useful library names:

- `NSC2Switch_MASTER_CHECKPOINT_2026-09-23_R84.md`
- `NSC2Switch_MASTER_CHECKPOINT_2026-09-25_R126.md`
- `NSC2Switch_MASTER_CHECKPOINT_2026-09-25_R128.md`
- `P128_TOBI_VOICE_AUDIT_R145.txt`
- `R28_EXACT_INPUTS_AUDIT.txt`
- `R33_PRM_STRING_VOICE_PARITY_AUDIT.txt`
- `build_r30_dpad_charge100.py`
- `NSC2Switch_alpha14c_movesetplus_descriptor_v22.txt`
- latest `uzuy_log(...)`
- latest V2 source/artifact ZIPs

When a source package is referenced but not attached:
- search the Library before asking the user to re-upload.

---

# 31. CHECKPOINT UPDATE POLICY — MANDATORY FROM NOW ON

At the end of every meaningful iteration, create/update BOTH:

1. versioned checkpoint:
   `NSC2Switch_MASTER_CHECKPOINT_YYYY-MM-DD_R###_FULL.md`

2. canonical latest checkpoint:
   `NSC2Switch_MASTER_CHECKPOINT_LATEST.md`

The checkpoint must always include:
- identity/build/hash data;
- baseline invariants;
- complete lineage from the beginning;
- latest source ZIP name/hash;
- latest compiled artifact name/hash;
- latest deployed main/runtime hashes;
- exact test result;
- PASS/FAIL state;
- new runtime markers;
- new proven facts;
- retired hypotheses;
- unresolved bugs;
- precise next frontier;
- test instructions for the next build.

Never replace the checkpoint with a tiny delta-only note.
The canonical file must remain a **complete standalone recovery document**.

---

# 32. CROSS-SESSION / CROSS-MODEL / CROSS-ACCOUNT PERSISTENCE

Same account:
- storing this file in the ChatGPT Library makes it recoverable from new sessions/models.

Different account:
- Library storage is account-scoped.
- A different account will not automatically have this project history.
- Therefore the user should also keep/download a copy of the latest checkpoint externally (Drive/local storage/repo) if true cross-account recovery is required.

The checkpoint itself is the portable source of truth.

---

# 33. CURRENT HANDOFF STATEMENT

As of R147:

**Infrastructure status**
- V2D original-main runtime patch architecture is hardware-proven.
- main-file replacement dependency has been removed for the current v1.70 proof.
- subsdk9 remains only as the bootstrap and should not be removed yet.

**Gameplay status**
- Tobi own UJ works and returns control.
- Naruto UJ safe.
- victim UJ safe.
- other jutsu still work after Tobi UJ.
- D-pad Right still wrong: disappears instead of visible Sharingan/invulnerability.
- UJ map transition still visually mixed.
- voice/audio parity still missing/incomplete.
- awakening parity still backlog.

**Next exact target**
- D-pad Right semantic parity on V2D, starting from proven runtime chain:
  `action928 -> EVT236 op23 SPTYPE_ACTION10 -> action930`.

Do not reopen solved UJ-admission hypotheses unless new runtime evidence forces it.

# 34. V2E — D-PAD RIGHT / OPCODE17 SOURCE-PARITY STAGE 1

Parent:
- hardware-PASS V2D original-main runtime architecture.

Source package:
- `NSC2Switch_RUNTIME_V2E_DPAD17_SOURCE_PARITY_DROPIN.zip`
- SHA256: `aa21839b19c6ffd9826e204ed6ed58c0781b236e3d47005162b6e89289beef64`

Source verifier:
- `NSC_RUNTIME_V2E_SOURCE_VERIFY=PASS`
- verifier was rerun after extracting the final ZIP and PASSed.

V2E does **not** replace the original-main V2D architecture. It changes only the missing Event236 opcode17 semantics.

## 34.1 New external reference confirming intended Izanagi behavior

The Tobi v1.2 mod description confirms the intended Right D-Pad behavior:
- Right D-Pad activates Izanagi if activation succeeds;
- Tobi should take no damage for about one minute;
- the Substitution Gauge automatically recovers during that minute;
- Ultimate Jutsu can dispel the effect;
- Left D-Pad cancels/resets Izanagi by replacing the left Sharingan.

The user also provided a YouTube showcase URL as visual reference:
- `https://youtu.be/nrORkcnzm7M?si=BNGPFYZRumRLi2mp`

Direct YouTube fetch was unavailable in the current web environment, so the implementation target is grounded in the mod's public description plus local source/runtime evidence. Do not invent unobserved visual details from the inaccessible video.

## 34.2 Exact latest V2D runtime evidence before V2E

Right D-Pad sequence in `uzuy_log(26).txt`:
- Tobi reaches action928.
- Event236 opcode23 resolves `SPTYPE_ACTION10` with param3=77.
- PlayAction transitions action928 -> action930.
- condition `SW_MTOB_XH` executes.
- while in action930, Event236 opcode17 fires with:
  - p2=0 (self)
  - p3=4 (Right arrow)
  - p4bits=`42c80000` = 100.0f
- V2D then emits `OP17_SHADOW`, proving the D-pad charge event is reached but discarded.

This makes opcode17 a causal, source-proven parity gap.

## 34.3 PC source contract

UltimateStormAPI / MovesetPlus SC1.70:

`me_change_dpad_charge(char_p, enemy, arrow, charge)`
- base = actor+0x12B88 on PC SC1.70;
- arrow0 -> write all 4 fields;
- arrow1 -> Up +0;
- arrow2 -> Down +4;
- arrow3 -> Left +8;
- arrow4 -> Right +12;
- no abs(charge)<=16 cap exists.

Prior Switch layout audit established the corresponding Switch D-pad block at:
- actor+`0x12B78`
- therefore Right charge is actor+`0x12B84`.

Historical R30 already proved the old experimental <=16 guard rejected valid Tobi charge=100 and was not source-parity.

## 34.4 V2E exact implementation

New generic helper:
- `HandleDpadChargeSourceParity(actor, enemy, arrow, charge)`

Behavior:
- accepts selector p2 0=self / 1=enemy;
- accepts arrow p3 0..4;
- writes raw float charge with no 16.0 clamp;
- no char281 branch;
- logs before/after values;
- keeps opcode12 visibility shadow unchanged;
- keeps opcode23 behavior unchanged for this A/B;
- keeps UJ/P128/V2D runtime patch architecture unchanged.

Expected marker:
`[NSC:V2E] DPAD17_APPLY ... enemy=0 arrow=4 charge_bits=42c80000 ... base_off=0x12b78 source_parity=1`

For the real Tobi Right-DPad activation, the fourth `after` field should become:
- `42c80000` (100.0f)

## 34.5 V2E decision tree

A. No `DPAD17_APPLY` marker
- event routing regressed or the tested sequence is not reaching opcode17.

B. Marker present, Right field becomes100, Izanagi works
- opcode17 was the missing causal piece.

C. Marker present, Right field becomes100, but Tobi still disappears / takes damage
- opcode17 is fixed;
- next target is opcode23 / animation semantics and SPTYPE_ACTION10 lifecycle.

Important PC source fact for that next branch:
- `me_play_action` does `SetActionImmediate(player_ptr, action)` and then calls `me_play_pl_anm`.
- `me_play_pl_anm` resolves a PlAnm index from `PlAnmList` and calls `ccPlayer::SetAnmDirect`.
- current Switch implementation still resolves the string and calls PlayAction, which may not be exact source parity.
- do not change this until V2E hardware result says opcode17 alone is insufficient.

## 34.6 V2E hardware test order

1. Fresh boot; confirm original-main V2D runtime patch markers still PASS.
2. Naruto own UJ once.
3. Tobi as victim UJ once.
4. Tobi own UJ once and verify return to control.
5. Press Right D-Pad once.
6. Observe Sharingan/Izanagi visual behavior and whether Tobi stays visible.
7. Let enemy hit Tobi repeatedly; verify whether HP damage is prevented.
8. Observe substitution gauge recovery.
9. Save the full log before Left D-Pad, restart, or additional state-reset experiments.

## 34.7 Current exact frontier after source build

Waiting for V2E hardware log/artifact.

Do not reopen solved UJ admission work unless V2E causes a regression.

---
END OF R147 FULL CHECKPOINT


# 35. R148 — V2E RESULT AND V2F OPCODE23 CAUSAL A/B

## 35.1 Files audited this iteration

1. `NSC-RUNTIME-V2E-dpad17-source-parity.zip`
   - SHA256 `5d06886fd17586573eaba2776e8bb7b62aa298078060fed052949013ad0663d4`
   - contains exactly the original main, V2E `subsdk9`, restore main, and SHA256 manifest.
   - deployed main/restore hash is the locked original `2579...ecd9`.
   - deployed V2E subsdk9 hash is `52e14893276354c02a8d7c9a192d660013db67d36d9a8f0bb20ff2bd20f65d04`.

2. `uzuy_log(27)(1).txt`
   - SHA256 `87644f135f9cd052dea204f417659365f83129b9bc150d7000ad215ec197f139`.
   - full-file marker census was performed, not only a local D-pad snippet.

3. `NSC2Switch_MASTER_CHECKPOINT_2026-09-26_R147_FULL.md`
   - SHA256 `b0c784a93107a40fba2311c3eaf1755006f061b0e6ee2f568cf3f0ce34a88fff`.
   - all locked invariants remain active.

4. Canonical V2E source package recovered from Library:
   - `NSC2Switch_RUNTIME_V2E_DPAD17_SOURCE_PARITY_DROPIN.zip`
   - SHA256 `aa21839b19c6ffd9826e204ed6ed58c0781b236e3d47005162b6e89289beef64`.
   - its source verifier passes the original main hash, exact P128 reference hash, exact 30-word delta, and all seven resolver signatures.

5. Original `UltimateStormAPI-main.zip` recovered from Library and inspected for the exact PC MovesetPlus contract.

## 35.2 Full latest-log census relevant to runtime

NSC prefix counts in the latest run include:
- P81A 4710
- P93A 4201
- P94A 1789
- P50A 1551
- P95A 1111
- P59A 289
- P55A 169
- P57A 133
- V2D 18
- V2E 4
- P128A 3

Custom Tobi Event236 opcode counts:
- op2 = 4
- op3 = 31
- op8 = 2
- op12 = 33
- op13 = 32
- op14 = 373
- op15 = 1
- op17 = 4
- op23 = 1
- op26 = 7

No runtime marker indicates:
- trampoline allocation failure;
- resolver failure;
- runtime patch failure;
- fingerprint failure;
- fail_closed=0.

## 35.3 V2E opcode17 verdict — CLOSED / PASS

Four opcode17 source-parity applications occur. Earlier rows write zero; the actual Right-DPad activation finally writes:
- enemy=0
- arrow=4
- charge_bits=`42c80000`
- before=`0/0/0/0`
- after=`0/0/0/42c80000`
- base_off=`0x12b78`

This is exact raw `100.0f` in the Right field. The old <=16 hypothesis is retired.

## 35.4 Opcode23 first proven semantic mismatch

Latest activation:
1. current action=928;
2. Event236 opcode23: `p2=0 p3=77 text=SPTYPE_ACTION10`;
3. PL_ANM name resolver: index930;
4. `SetActionImmediate(target,77)` executes, visible through E94=77;
5. current Switch compatibility code then calls `PlayAction(target,930)`;
6. central setter changes current action `928 -> 930`;
7. E94 remains77, producing a hybrid state that PC source does not create.

Exact PC source contract:
- `me_play_action`: resolve self/enemy; `ccPlayer::SetActionImmediate(player_ptr, action)`; then `me_play_pl_anm(...)`.
- `me_play_pl_anm`: resolve `pl_anm_id` from `PlAnmList`; if found, call `ccPlayer::SetAnmDirect(player_ptr, pl_anm_id)`.

Thus **930 is a PL_ANM index, not the action value for opcode23**.

## 35.5 Why visibility forcing is rejected

The latest log contains 33 Tobi visibility-shadow events and every one is `p2=1`. The custom compatibility path is being asked to keep/show the actor, not hide it. A global visible=1 patch would therefore not address the first proven semantic mismatch and would threaten P50 victim safety.

## 35.6 Switch SetAnmDirect status

- `0x7A8438` is statically/runtime-supported as the Switch immediate-action mechanism.
- `0x766B8C` is the full PlayAction path and is definitely too strong to stand in for SetAnmDirect.
- The exact Switch SetAnmDirect function has **not** yet been uniquely resolved.
- Simple PC-to-Switch absolute-offset translation is invalid; a candidate derived that way landed inside unrelated code and was rejected.
- Final opcode23 parity must remain fail-closed until the direct-animation target is uniquely identified/validated.

## 35.7 V2F source A/B prepared

Package:
- `NSC2Switch_RUNTIME_V2F_OP23_NO_PLAYACTION_AB_DROPIN.zip`
- SHA256 `33c73a2c20b5bbf717134f5a308e88cf6f6c12b8519154d51d02d93a81bb4a69`
- 30 files; source verifier PASS.

V2F changes only the opcode23 resolved-animation tail:
- `SetActionImmediate(param3)` remains;
- PL_ANM string lookup remains;
- opcode23 `PlayAction(resolved_pl_anm_index)` is suppressed;
- opcode22 remains the unchanged control path;
- op17 V2E source-parity remains;
- no visibility write is added;
- no guessed SetAnmDirect pointer is added;
- no char-specific runtime branch is added.

Expected marker:
`[NSC:V2F] OP23_NO_PLAYACTION_AB ... action_param=77 text=SPTYPE_ACTION10 pl_anm_index=930 ... playaction_suppressed=1 setanmdirect_unresolved=1 diagnostic_only=1`

## 35.8 V2F decision tree

A. Tobi no longer disappears after Right D-Pad:
- prove wrong `PlayAction(930)` is causally responsible for disappearance;
- next task: uniquely resolve/validate Switch SetAnmDirect and replace suppression with exact direct-animation call.

B. Tobi still disappears:
- wrong PlayAction930 is not the first disappearance cause;
- next trace must isolate action928 / immediate action77 / paired condition-event sequence before opcode17.

In either outcome:
- do not revisit opcode17;
- do not force visibility globally;
- do not reopen UJ admission;
- do not add char281 final logic.

## 35.9 Next hardware test — minimal

1. Build V2F through the included GitHub Actions workflow.
2. Fresh boot; confirm V2D resolver 7/7 + 30-word patch READY.
3. Press Right D-Pad once.
4. Confirm V2F marker with `action_param=77` and `pl_anm_index=930`.
5. Observe one fact first: does Tobi disappear?
6. Save the complete log immediately.
7. Only after saving, run UJ regression if needed.

# 36. V2F HARDWARE RESULT — OP23 PLAYACTION SUPPRESSION A/B

Date: 2026-09-27

User hardware/emulator evidence:
- log: `uzuy_log(28).txt`
- compiled artifact: `NSC-RUNTIME-V2F-op23-no-playaction-ab.zip`
- artifact ZIP SHA256: `2c60ba83ef7e234fffbcd3495f0639bc9a2a2fc3db66877d3e26a90bbd6b074f`
- deployed original `main` SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- deployed V2F `subsdk9` SHA256: `757c2ebea72fc16898dd10b4979dfb86414614ddfc1a2fc0f270f695ad917e88`

## 36.1 Infrastructure verdict

V2F boots cleanly on the original-main V2D architecture:
- resolver `7/7`, `fail_closed=1`, `original_main=1`;
- runtime patch `words=30`;
- EVENT236 / PLAY_ACTION / CENTRAL_SETTER / CPK_BIND / CHARACODE_GETTER hooks installed;
- P67/P81/P128 remain ready;
- opcode17 source-parity implementation remains enabled.

No evidence of deployment mismatch exists in this run.

## 36.2 Hardware observation

User-reported result:
- Right D-Pad no longer makes Tobi disappear.
- Tobi still takes normal damage; Izanagi protection is therefore not active.
- A reset/cancel behavior was observed; authoritative mod behavior must distinguish Right vs Left D-Pad.

This resolves the V2F A/B branch as:

**V2F A/B = PASS for disappearance causality, FAIL as a final Izanagi implementation.**

The wrong opcode23 `PlayAction(930)` substitution is causally involved in the disappearance. Suppressing it removes the disappearance.

## 36.3 Runtime proof from log28

The V2F opcode23 marker occurs five times. Each activation has the same essential state:
- current action before opcode23 = 928;
- Event236 opcode23: `p2=0`, `p3=77`, text=`SPTYPE_ACTION10`;
- PL_ANM resolver returns index930;
- `SetActionImmediate(77)` succeeds (`E94=77`);
- `PlayAction(930)` is suppressed;
- current action remains928;
- marker explicitly reports `setanmdirect_unresolved=1 diagnostic_only=1`.

Representative marker:
`[NSC:V2F] OP23_NO_PLAYACTION_AB ... action_param=77 text=SPTYPE_ACTION10 pl_anm_index=930 current_action=928 e94=77 ... playaction_suppressed=1 setanmdirect_unresolved=1 diagnostic_only=1`

Critically, unlike V2E, this player-side V2F activation does **not** proceed to the real Izanagi activation tail:
- no player-side opcode17 Right charge=`100.0f` follows these five opcode23 activations;
- the only V2F `DPAD17_APPLY` for char281 is an unrelated/reset-side event with charge bits `00000000`;
- therefore the Right-DPad charge/state protection is never armed in V2F.

The last activation is followed by a normal state transition `928 -> 251` when Tobi is struck, consistent with the user's observation that incoming damage/reaction is still accepted. Do not label action251 semantically without a separate proof; it is only evidence that the actor remains damage-reactive.

## 36.4 Why V2F does not provide invulnerability

V2F intentionally removed the incorrect full `PlayAction(930)`, but it did not replace it with the PC source operation `SetAnmDirect(930)`.

PC source contract remains:
1. `SetActionImmediate(player, 77)`;
2. resolve `SPTYPE_ACTION10` in `PlAnmList` -> 930;
3. `SetAnmDirect(player, 930)`.

In V2E, the incorrect full action930 route eventually caused the `SPTYPE_ACTION10` animation/event stream to emit:
- `SW_MTOB_XH` Event121;
- Event236 opcode17 Right charge=`100.0f`.

In V2F, suppressing PlayAction930 also removes that downstream animation/event stream. This is why disappearance is gone while Izanagi protection is not activated.

Do **not** respond by globally forcing no-damage, visibility, or Right charge. Those would mask the missing direct-animation semantics rather than port them.

## 36.5 Authoritative intended D-Pad behavior

The Tobi v1.2 mod description by jackwans defines:
- **Right D-Pad:** activates Izanagi. On successful activation, Tobi takes no damage for approximately one minute and the Substitution Gauge automatically recovers during that minute. Ultimate Jutsu can dispel the effect.
- **Left D-Pad:** teleports Tobi to the secret room to replace the left Sharingan; this cancels Izanagi and resets Izanagi.

Therefore:
- Right D-Pad is **activation**, not reset.
- Left D-Pad is **cancel/reset**.

The author currently links showcase video `https://b23.tv/HmLyGTO`. The current analysis environment could confirm the link from the mod description but could not fetch/play the short-video destination, so no unobserved visual details are asserted.

## 36.6 Static SetAnmDirect search update

A full-main scan was started using the exact PC call contract as a structural clue.

Important rejection:
- a naive PC->Switch delta candidate around `0x7650C8` is invalid; it lies inside a larger function beginning around `0x764F38`, and the surrounding function treats its arguments as structured pointers rather than `(player, animation index, ...)`.
- a later six-argument-pattern scan produced target `0x725050`, but inspection showed its matching callsites overwrite the candidate argument state and pass many additional parameters; `0x725050` is therefore **not proven SetAnmDirect** and must not be used.

Exact Switch `SetAnmDirect` remains unresolved as of R149.

## 36.7 Exact next frontier

Next implementation target is now singular:

**Resolve and validate the real Switch v1.70 direct-animation entry used for the equivalent of `ccPlayer::SetAnmDirect`, then replace V2F diagnostic suppression with:**

`SetActionImmediate(target, param3)` -> `SetAnmDirect(target, resolved_pl_anm_index)`

Acceptance criteria for the first parity build after resolution:
1. Tobi enters action928 as before.
2. opcode23 receives p3=77 / `SPTYPE_ACTION10`.
3. E94 becomes77.
4. PL_ANM index930 is applied through direct animation, **without current action becoming930**.
5. animation/event stream reaches `SW_MTOB_XH` and opcode17 Right=`100.0f` naturally.
6. Tobi remains visible.
7. normal incoming hits do not reduce HP for the intended Izanagi duration.
8. substitution gauge recovers automatically during the effect.
9. Ultimate Jutsu can dispel the effect.
10. Left D-Pad cancels/resets Izanagi and performs the intended eye-replacement/secret-room sequence.
11. Naruto UJ, Tobi victim UJ, Tobi own UJ, post-UJ movement/jutsu remain PASS.

Do not reopen opcode17 clamp, global visibility, UJ admission, or char281 hardcoding unless new evidence contradicts the current proof.



---

# 37. V2G STATIC RESOLUTION — OPCODE23 DIRECT ANIMATION

Date: 2026-09-27

Prepared source artifact:
- `NSC2Switch_RUNTIME_V2G_OP23_DIRECT_ANM_DROPIN.zip`
- SHA256 `4e0880d9a608f8d446f124bc7bf1193b6cbe51ecf9217233cc8ad7f1e48deb66`
- verifier: `NSC_RUNTIME_V2G_SOURCE_VERIFY=PASS`
- source package remains original-main deployment; reference P128 main is retained only as verifier input for the exact known 30-word runtime delta.

## 37.1 Correction to historical P57 interpretation

P57 source read the observed field with:

`*(actor + 4712)`

4712 decimal is `0x1268`, not an EAx action field. Therefore old labels such as `pre_action/post_action` at P57 were semantically wrong. V2G renames the P57 trace output to `anm1268` and treats it as animation state.

This does **not** invalidate the old runtime measurements. It corrects what those measurements represented.

## 37.2 Static proof: SetActionImmediate is separate

At `main+0x7A846C..0x7A8474`, inside the established `main+0x7A8438` routine:
- load old actor+`0xE94`;
- store requested `w1` to actor+`0xE94`;
- store old E94 to actor+`0xE98`.

Verifier locks exact words beginning at `0x7A8464`:
`52808D09 72A00029 B94E940A B90E9401 B90E980A`

This proves action request (`E94`) is independent from direct animation state (`1268`).

## 37.3 Static proof: main+0x766320 is direct-animation core

Unique existing resolver anchor `CENTRAL_SETTER` resolves on the original v1.70 main to:
- `main+0x766320`
- unique hit count = 1.

Entry facts:
- `MOV V8.16B,V0.16B` preserves incoming float `s0`;
- `w3 -> w20`;
- `w2 -> w22`;
- `x0 -> x19`;
- `w1 -> w21`.

Successful tail at `0x766A50`:
- `STR w8,[x19,#0x1264]` -> animation-valid state;
- `STR w8,[x19,#0x1270]` -> timing/duration;
- `STR w21,[x19,#0x1268]` -> selected animation index;
- `STR s8,[x19,#0x126C]` -> incoming float rate;
- `STR w20,[x19,#0x1274]` -> auxiliary integer arg.

Verifier locks exact tail words:
`B9126668 1E380008 B9127268 F9410E68 B9126A75 BD126E68 B9127674 B900311F`

## 37.4 Native-callsite ABI proof

Multiple unrelated game callsites invoke `0x766320` directly with the same pattern:
- `FMOV S0,#1.0`;
- `W1 = animation index`;
- `W2 = -1`;
- `X0 = actor`;
- `W3 = 0`;
- `BL 0x766320`.

Locked examples in the verifier:
- `main+0x79A98`: animation936, exact sequence ends `BL 0x766320`;
- `main+0x7B638`: animation934, exact sequence ends `BL 0x766320`.

Additional manually audited examples include animation938, 940, 942/943, and74 with the same ABI.

Thus V2G direct call type is:
`void (*)(void* actor, int32_t animation, int32_t a2, int32_t a3, float rate)`

and opcode23 calls:
`(target, resolved_pl_anm_index, -1, 0, 1.0f)`.

## 37.5 Why 0x766B8C caused the V2E disappearance

Static wrapper split at `main+0x766BC4` is locked by verifier:
`F9400268 AA1303E0 F947CD08 D63F0100 AA1303E0 2A1403E1 52800022 94000033`

Semantics:
1. load actor vtable;
2. call vtable+`0xF98`;
3. locked vtable relocation identifies that target as `main+0x766320`;
4. then call extra routine `main+0x766CAC`.

Therefore old opcode23 `PlayAction(930)` was not merely "animation930". It performed the needed direct animation and then a stronger second-stage PlayAction transition. V2F proved suppressing the whole wrapper removes disappearance, while also removing the needed animation chain.

V2G isolates only the first/native direct-animation operation.

## 37.6 P57 trampoline ABI fix

Because `0x766320` receives rate in `s0`, the historical P57 hook callback prototype with only four integer arguments was incomplete and could not guarantee preservation of `s0` across tracing before `Orig(...)`.

V2G changes the callback to:
`Callback(actor, animation, a2, a3, float rate)`

and forwards:
`Orig(actor, animation, a2, a3, rate)`.

This keeps the existing diagnostic hook architecture while making it ABI-correct for direct animation.

## 37.7 V2G opcode23 implementation

Opcode23 path only:
1. capture E94 / ANM1268 before state;
2. call established `SetActionImmediate(target,param3)`;
3. resolve PL_ANM string exactly as before;
4. get `Anchor::CentralSetter` through the V2 resolver;
5. fail closed if resolver target is unavailable;
6. call direct animation `(target,index,-1,0,1.0f)`;
7. log post `1264`, `1268`, `E94`, `E98`;
8. return without calling the PlayAction wrapper.

Dedicated marker:
`[NSC:V2G] OP23_DIRECT_ANM ... direct_off=0x766320 ... direct_args_m1_0_rate1=1 playaction_wrapper=0 stage2_766cac=0 source_parity_candidate=1`

Opcode22 intentionally stays on its old path for this one hardware A/B.

## 37.8 Source verifier result

All V2D/V2E invariants remain PASS:
- original main SHA;
- reference P128 main SHA;
- exact 30-word delta;
- seven unique original-main resolver signatures;
- D-pad17 source parity;
- no char281 runtime branch;
- no guessed `kSetAnmDirectOffset`;
- UJ gate/post dynamic resolver architecture.

New V2G checks PASS:
- direct marker present;
- direct target obtained via resolver CentralSetter;
- native direct ABI is `-1,0,1.0f`;
- opcode23 direct branch contains no PlayAction wrapper call;
- P57 float ABI preserved;
- direct entry exact words;
- direct state-write tail exact words;
- wrapper split exact words;
- native animation936 caller exact words;
- native animation934 caller exact words;
- SetActionImmediate E94/E98 writes exact words.

Final verifier marker:
`NSC_RUNTIME_V2G_SOURCE_VERIFY=PASS`

## 37.9 Next hardware test — minimal and causal

Build the V2G drop-in through its included GitHub Actions workflow (`NSC-RUNTIME-V2G-op23-direct-anm`). Then:

1. fresh boot;
2. confirm V2 resolver `7/7`, `fail_closed=1`, runtime patch 30 words;
3. press Right D-Pad once;
4. expect opcode23 `p3=77`, `SPTYPE_ACTION10`, index930;
5. expect `[NSC:V2G] OP23_DIRECT_ANM` with `direct_off=0x766320`, `anm1268 ... ->930`, E94 ->77;
6. verify Tobi does not disappear;
7. verify natural downstream `SW_MTOB_XH` appears;
8. verify natural opcode17 Right write reaches `42c80000` /100.0f;
9. let enemy land repeated normal hits and observe HP plus substitution gauge;
10. save full log immediately.

Primary PASS target:
- Tobi stays visible;
- normal hits do not reduce HP during active Izanagi;
- substitution gauge recovery occurs naturally.

If the direct marker reaches930 but `SW_MTOB_XH`/opcode17 do not occur, trace downstream animation events next. Do not force invulnerability/visibility manually.

---
END OF R150 FULL CHECKPOINT

# 38. V2G HARDWARE RESULT — FULL PL_ANM930 PATH UNSAFE (SEMANTIC CLASSIFICATION LATER CORRECTED IN R152)

Date: 2026-09-27

User inputs:
- compiled artifact `NSC-RUNTIME-V2G-op23-direct-anm.zip`
- runtime log `uzuy_log(29).txt`
- user observation: Right D-Pad makes Tobi disappear again; Tobi UJ still mixes the normal battle map into the cinematic; Tobi UJ still has no sound.

## 38.1 Deployment/infrastructure proof

The tested artifact is the intended V2G build, not a stale deployment:
- artifact ZIP SHA256 `63c79f23dccef4e47018156e0259c0f3ed5c69a784809fb152c198fc56fc1295`;
- original deployed main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`;
- V2G subsdk9 SHA256 `8b905a316066984453ba9bd23e3b3c39526f69734d49208516e4dd251512a648`.

Runtime boot remains healthy:
- resolver7/7, fail_closed=1, original_main=1;
- runtime patch words=30;
- dynamic EVENT236/PLAY_ACTION/CENTRAL_SETTER/CPK/CHARACODE/UJ hooks installed;
- P128 remains ready.

Therefore the gameplay result is valid evidence against the V2G hypothesis.

## 38.2 Decisive opcode23 evidence

At the Right-DPad activation:
1. pre-state/action field1268 =928;
2. Event236 opcode23 receives p3=77, text=`SPTYPE_ACTION10`;
3. PL_ANM lookup resolves index930;
4. SetActionImmediate writes E94=77;
5. V2G calls `main+0x766320` with index930;
6. P93 phase0 sees action/state928;
7. P93 phase1 sees action/state930;
8. P57 reports field1268 `928->930`;
9. user observes Tobi disappear.

This is the same poisonous transition V2F avoided.

**R151-era hardware verdict (refined by R152):**
Using `main+0x766320` to drive PL_ANM930 is NOT yet behaviorally safe because it reproduces Tobi disappearance. However, R152 corrects the interpretation of field `0x1268`: it is animation state, so the observed `928->930` transition is expected for a direct animation call and does not by itself prove that `0x766320` is the wrong low-level animation primitive. What remains proven is that the full PL_ANM930 path exposes an unresolved visual/lifecycle parity bug.

## 38.3 Downstream Izanagi chain still proves opcode17

About two seconds after the bad 928->930 transition, V2G reaches:
- Event121 `SW_MTOB_XH`, executed=1;
- Event236 opcode17 p3=4, p4=100.0f;
- V2E source-parity write sets the Right field to `42c80000`.

Thus:
- 0x766320 is sufficient to drive the SPTYPE_ACTION10 event stream;
- the stream reaches the correct `SW_MTOB_XH` + opcode17 Right=100 activation tail;
- opcode17 remains correct and is not the disappearance cause;
- the disappearance is somewhere in the full PL_ANM930 visual/lifecycle path, not proven to be the `0x1268=930` animation-state assignment itself.

The unresolved D-pad target is therefore:
preserve the source activation semantics while isolating the part of the full PL_ANM930 path that makes the Switch custom actor visually disappear.

## 38.4 UJ admission remains solved

During the same V2G run:
- P124 bridges raw15;
- P128 POST_OUTER returns1;
- session_latch=1;
- action707 naturally progresses to action710.

User's stage/audio issues are downstream of admission. Do not modify raw15 gate/session policy for these symptoms.

## 38.5 UJ stage request is definitely emitted

At action710 the custom event stream reaches:
`Event236 op2 p2=0 text=STG_2TOB_UNI_LT`.

The original Tobi `.unse` contains:
- `Stages/STG_2TOB_UNI_LT/data/stage/StageInfo.bin.xfbin`;
- `Stages/STG_2TOB_UNI_LT/stage_config.ini`.

Therefore the remaining map mixture is not explained by absence of a stage request or absence of authored stage files in the source package.

Current Switch HandleStageMove still needs runtime proof at each step:
- StageMove manager/object/context lookup;
- specific handler CRC application;
- stage state ID before/after handler;
- HandleStageChange;
- actor/enemy position repair.

Known source-parity discrepancy:
- PC 1.70 source calls FixCharPosition(player) AND FixCharPosition(enemy);
- current Switch port calls FixCharPosition(actor) only;
- current Switch port additionally calls PostStage(), which is not present in the PC helper source.

Do not mutate these differences before the V2H trace proves where stage switching stops/fails.

## 38.6 UJ sound events are definitely emitted

V2G action710 reaches opcode26 generic sound events:
- `S_PL_etc_l` (source NSC_SFX index21 => command0x7015);
- `S_PL_DMG_cmn_vS_rv` (index153 => command0x7099), targeted to enemy with p2=1;
- `S_PL_etc_m` (index22 => command0x7016).

A later generic opcode26 `S_PL_ATK_throw_v2` is also reached.

Current custom Event236 dispatcher does not implement opcode26, so these calls are swallowed.
This directly explains missing generic UJ SFX/reaction cues.

Separately, dedicated Tobi voice/dialogue is an Event150/sound-bank registration problem:
- PRM references `mtob_ougi_001/002/003`;
- `.unse` ships mtob sound event and JP voice assets;
- Character Sound Entries/ACB support remains unported.

Do not conflate generic opcode26 SFX with dedicated mtob Event150 voice cues; both must eventually work.

## 38.7 V2H prepared

Source package:
`NSC2Switch_RUNTIME_V2H_SAFE_OP23_STAGE_AUDIO_PROBE_DROPIN.zip`
SHA256:
`ca14725655e4d9b748b266120274d221ae0a87d65e293564c072af7db9f7d40b`
Verifier:
`NSC_RUNTIME_V2H_SOURCE_VERIFY=PASS`

V2H changes:
1. **D-pad safety rollback:** opcode23 returns to V2F behavior after SetActionImmediate+PL_ANM lookup; no 0x766320 and no PlayAction930 call.
2. **Stage trace:** logs `STAGE2_ENTER`, explicit `STAGE2_FAIL reason=...`, or `STAGE2_DONE` with CRC and stage IDs before/after.
3. **Audio probe:** opcode26 resolves exact source NSC_SFX index and command and logs runtime vtable slots +0x1000/+0x1010/+0x1020/+0x1030, but performs zero playback.
4. No global visibility/no-damage force.
5. No guessed direct-animation pointer.
6. No char281 gameplay branch.
7. UJ/P128 architecture unchanged.

## 38.8 Minimal V2H hardware test

One fresh boot is enough:
1. Tobi Right D-Pad once — verify he stays visible (rollback sanity).
2. Tobi own UJ once — allow the whole cinematic to complete.
3. Save full log immediately.

Required next markers:
- `[NSC:V2H] OP23_SAFE_SUPPRESS ...`
- `[NSC:V2H] STAGE2_ENTER ... text=STG_2TOB_UNI_LT ...`
- either `[NSC:V2H] STAGE2_FAIL ...` or `[NSC:V2H] STAGE2_DONE ...`
- `[NSC:V2H] OP26_PROBE ... text=S_PL_etc_l ...`
- corresponding OP26 probes for `S_PL_DMG_cmn_vS_rv` and `S_PL_etc_m`.

Decision after V2H:
- STAGE2_FAIL identifies the exact broken pointer/lookup boundary.
- STAGE2_DONE with unchanged stage ID proves custom stage registration/CRC lookup gap.
- STAGE2_DONE with changed stage ID but mixed map shifts focus to HandleStageChange/PostStage/environment ownership.
- OP26 runtime slots + source index will determine the safe Switch sound-call target; do not guess from PC +0x1020.

END OF R151 ADDENDUM



# 39. V2H HARDWARE RESULT + V2I PREPARATION — R152

Date: 2026-09-27

User inputs:
- compiled artifact `NSC-RUNTIME-V2H-safe-op23-stage-audio-probe.zip`;
- runtime log `uzuy_log(30).txt`;
- user observation: Right D-Pad no longer makes Tobi disappear, but enemy jutsu/hits still appear to reduce HP.

## 39.1 Exact deployment proof

Latest log SHA256:
`42cf74ca5e2c5c39398ac7d5e93b84b5417dabd97ab1b7a5c171fe675a7d9767`

Compiled V2H artifact SHA256:
`95e59828d687222649c11348d2084e90caa194fef3fe60a7687501873930375a`

Deployed files:
- main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9` (locked original);
- subsdk9 SHA256 `f8a036a810db83520c36f6d6f83d30a1102171884058bbf1848742e95e567506`;
- restore main identical to original.

Boot/runtime infrastructure remains healthy:
- resolver 7/7, fail_closed=1, original_main=1;
- runtime patch exact 30 words;
- P128 ready;
- no deployment mismatch.

## 39.2 Right-DPad verdict: visibility PASS, Izanagi activation tail absent

At the tested activation V2H logs:
- Event236 opcode23 p3=77 / `SPTYPE_ACTION10`;
- PL_ANM lookup index930;
- `OP23_SAFE_SUPPRESS` keeps animation state `0x1268` at 928;
- E94 changes 152->77 through SetActionImmediate;
- no call to 0x766320 and no PlayAction wrapper.

Critically, the complete log30 contains:
- **zero Event236 opcode17 records**;
- **zero `DPAD17_APPLY` records**.

Therefore V2H does not arm the Right-DPad `100.0f` charge at all. The user's observation that incoming jutsu still causes damage is consistent with the runtime evidence. This is not evidence that opcode17 is broken; opcode17 simply never executes in V2H because the source PL_ANM930 event stream is suppressed.

## 39.3 Exact SPTYPE_ACTION10 source event registry

Decoded Tobi PRM source SHA256:
`70c84800b92a398bc5a58be663c6337c724bed9786d46d1f65fcc2aee2be6f3a`

`PL_ANM_SPTYPE_ACTION10` has the following relevant native events:
- 159 `ME_ANM_SPEED_SET`;
- 33 `ME_FWDVELOCITY_SET`;
- 298 `ME_NOT_NOMALCOMBO_CAMERA_DIST`;
- 186 `ME_DMGHIT_OFF`;
- 184 `ME_BODHIT_OFF`;
- 32 `ME_JUMPVEL_SET`;
- 41 `ME_FLIGHT_BEGIN`;
- Event121 `ME_ADD_CONDITION_PARAM` -> `SW_MTOB_XH`;
- Event236 opcode17 -> self / Right /100.0f;
- 254 `ME_MOT_UPGRADE_CANCEL`;
- 42 `ME_FLIGHT_END`;
- 36 `ME_WARP_AROUND_ENEMY`;
- 299 `ME_NOT_NOMALCOMBO_CAMERA_DIST_RESET`;
- 183 `ME_BODHIT_ON`;
- 185 `ME_DMGHIT_ON`;
- 119 `ME_ACT_FALL`.

The native event names were recovered directly from Switch v1.70's 300-record event registry by parsing the NSO dynamic RELA table at record base `0x2077948`, stride24. This corrects an important interpretation: actor+`0x1268` is animation state. Therefore V2G's 928->930 write is expected for PL_ANM930 and is not sufficient proof that 0x766320 itself is the wrong low-level direct-animation primitive.

## 39.4 V2I controlled Izanagi activation-core A/B

Rather than forcing global invulnerability or visibility, V2I keeps the full animation930 path suppressed and replays only the exact source frame-13 activation pair for the current diagnostic fixture:
1. Event121 SELF condition `SW_MTOB_XH` using the established native condition owner/resolve/apply chain;
2. Event236 opcode17 exact payload `(enemy=0, arrow=4, charge=100.0f)` through the already-proven source-parity D-pad handler.

Guard is diagnostic-only:
- action_param=77;
- text=`SPTYPE_ACTION10`;
- no char281 check.

Marker:
`[NSC:V2I] IZANAGI_CORE_AB ... cond=SW_MTOB_XH ... right_bits=42c80000 animation930_suppressed=1 source_frame13_only=1 diagnostic_only=1`

Decision:
- if Tobi stays visible AND incoming hits stop reducing HP, the long-lived protection core is proven separable from the problematic visual animation path;
- if Tobi stays visible but still takes damage, the remaining protection depends on additional native events/state from `SPTYPE_ACTION10`, and we must not fake it with a no-damage flag.

## 39.5 Stage frontier resolved one layer deeper

V2H `STG_2TOB_UNI_LT` result:
- requested CRC `0x01D1CA7E`;
- stage ID changes from1770899245 to30526078;
- decimal30526078 == `0x01D1CA7E`;
- manager/object/context all non-null;
- HandleStageChange is called.

Therefore custom Kamui stage lookup/CRC registration is working. The battle-map mixture is downstream lifecycle parity.

V2H exposed two exact discrepancies from PC `MovesetPlus::me_test_switch_stage`:
- Switch port fixed actor only; PC fixes actor AND enemy;
- Switch port additionally called PostStage; PC source has no corresponding call.

V2I corrects both:
`HandleStageChange(stage_id) -> FixCharPosition(actor) -> FixCharPosition(enemy if non-null)`, with no extra PostStage call.

Marker:
`[NSC:V2I] STAGE2_PARITY ... fix_actor=1 fix_enemy=1 poststage=0 pc_source_parity=1`

## 39.6 Opcode26 generic sound path now statically proven

V2H runtime probes:
- `S_PL_etc_l`: source SFX index21, command0x7015;
- `S_PL_DMG_cmn_vS_rv`: index153, command0x7099, enemy target;
- `S_PL_etc_m`: index22, command0x7016.

Actor vtable slot +0x1030 resolves to `main+0x635DA0` for the tested actors.

Native Switch code at `main+0x813D88` provides an exact ABI proof:
- load signed event sound ID from event+0x24;
- add0x7000;
- load actor vtable+0x1030;
- set arg2=0;
- BLR the slot.

Locked instruction words:
`F81F0FFE 79C04828 11401D01 F9400008 F9481908 2A1F03E2 D63F0100 52800020 F84107FE D65F03C0`

V2I therefore ports opcode26 as:
`slot1030(target, sfx_index+0x7000, 0)`
with fail-closed main-range validation and no char-specific branch.

Marker:
`[NSC:V2I] OP26_PLAY ... command=... slot1030=... called=1 ... native_813d88_contract=1`

This restores generic SFX semantics only. Dedicated Tobi voice cues (`mtob_ougi_001/002/003`) still belong to Event150 / Character Sound Entries / ACB registration and remain a separate frontier.

## 39.7 V2I source artifact

Package:
`NSC2Switch_RUNTIME_V2I_ACTIVATION_CORE_STAGE_AUDIO_PARITY_DROPIN.zip`

SHA256:
`5f767fa945e8740ee119b67e39f68c26bc689f15e8c366e0ee1859f78ccd830f`

Verifier final marker:
`NSC_RUNTIME_V2I_SOURCE_VERIFY=PASS`

Locked verifier coverage includes:
- original main hash;
- reference P128 hash;
- exact 30-word runtime delta;
- resolver 7/7 signatures;
- safe opcode23 suppression;
- no char281 branch;
- source frame-13 diagnostic activation core;
- stage actor+enemy parity and no PostStage call;
- exact 160-entry SFX indices;
- exact native Switch +0x1030 sound callsite words at0x813D88.

## 39.8 Minimal V2I hardware test

Fresh boot, then in this order:
1. press Right D-Pad once;
2. verify Tobi stays visible;
3. let enemy land one normal hit and one jutsu; compare HP behavior;
4. observe whether substitution gauge recovers/counts as intended;
5. perform Tobi own UJ once;
6. observe whether Kamui environment still mixes with battle map;
7. listen for generic SFX during UJ;
8. save the full log immediately.

Required markers:
- `OP23_SAFE_SUPPRESS`;
- `IZANAGI_CORE_AB` with `right_bits=42c80000`;
- `STAGE2_PARITY` with `fix_enemy=1 poststage=0`;
- `OP26_PLAY` for the three known UJ generic cues.

Do not interpret still-missing `mtob_ougi_001/002/003` dialogue as failure of opcode26; dedicated voice registration is a separate subsystem.

END OF R152 ADDENDUM


# 40. V2I HARDWARE RESULT + V2J PREPARATION — R153

Date: 2026-09-27

User inputs:
- compiled artifact `NSC-RUNTIME-V2I-activation-core-stage-audio-parity.zip`;
- runtime log `uzuy_log(31).txt`;
- user observation: Tobi UJ now has sound; Kamui still visually mixes with the battle map; Right D-pad appears to affect the cells/substitution behavior only rather than full Izanagi.

## 40.1 Exact V2I deployment proof

Latest log:
- SHA256 `38a6586c5e095c016ade1b8bd3ddde85df1870930c139f1cdbd5c757e56d31c0`;
- 12064 lines.

Compiled V2I artifact:
- SHA256 `b4b429cda99d15e981fc3713a233fd485c71e36b42e1d1c398f15a5ae2115db0`.

Deployed files:
- main `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`;
- subsdk9 `5a034a499702892e446e289b2ff5a40abd85fbb68ce23d9b05d8e712f5462bbc`;
- restore main identical to locked original.

Therefore V2I hardware observations are valid for the intended build; there is no deployment mismatch.

## 40.2 Audio verdict: generic opcode26 hardware PASS

At the first Kamui stage request, log31 shows:
- `STG_2TOB_UNI_LT` request and successful stage-ID change;
- immediately following Event236 opcode26 `S_PL_etc_l`;
- V2I `OP26_PLAY` with index21, command0x7015, actor vtable+0x1030=`main+0x635DA0`, `called=1`.

Later UJ events also call:
- `S_PL_DMG_cmn_vS_rv` index153 / command0x7099;
- `S_PL_etc_m` index22 / command0x7016;
- later generic action SFX also use the same path.

User confirms Tobi UJ now has sound.

Decision:
- freeze opcode26 implementation;
- do not spend the next iteration on audio;
- dedicated Event150/ACB voice semantics are not separately proven complete, but they are no longer the active user-reported blocker.

## 40.3 Stage verdict: lookup and live stage ID PASS, environment lifecycle still FAIL

First custom stage transition in log31:
- request text `STG_2TOB_UNI_LT`;
- CRC `0x01D1CA7E`;
- manager/object/context are non-null;
- stage ID changes `1101369160 -> 30526078 -> 30526078`;
- `30526078 == 0x01D1CA7E`;
- actor and enemy are both passed through FixCharPosition;
- V2I marker explicitly records `poststage=0`.

Restore later changes stage ID from `0x01D1CA7E` back to `STAGE_SI45A` CRC `0x2BCB5498`.
A second UJ repeats the same successful custom-stage state-ID transition.

User nevertheless still sees the battle map mixed with Kamui.

Therefore:
- custom stage registration is NOT the frontier;
- CRC lookup is NOT the frontier;
- stage state-ID assignment is NOT the frontier;
- focus shifts to Switch-native post-transition/environment propagation.

### New static Switch proof

Original Switch main contains exactly the relevant native transition sequence:

```
0x48E344 BL 0x53643C
0x48E348 ADRP X8,...
0x48E34C LDR X8,[X8,#0x4C0]
0x48E350 LDR X8,[X8]
0x48E354 LDR W0,[X8,#8]
0x48E358 BL 0x6E8EB0
0x48E35C MOV X0,X19
0x48E360 BL 0x48E40C
0x48E364 BL 0x48E61C
```

So native Switch parity includes the call to `main+0x48E61C` immediately after HandleStageChange + FixCharPosition(actor).

`main+0x48E61C` itself iterates battle members through `0x880150` and calls `0x77FBF4(member,1)` on the returned members and related `+0x1238` objects. Its exact semantic name is still unknown, but it is statically proven to be part of the native Switch stage-transition sequence.

V2H had PostStage but fixed only actor.
V2I fixed actor+enemy but removed PostStage.
Neither produced correct visual Kamui.

V2J therefore tests the previously untested combination:
`HandleStageChange -> Fix actor -> Fix enemy -> main+0x48E61C`.

This is generic and contains no Tobi/281 condition.

## 40.4 Right D-pad verdict: source activation core executes, full Izanagi does not

At the V2I Right activation:
- opcode23 safely suppresses PL_ANM930 and keeps animation state928;
- E94 becomes77;
- exact source-parity opcode17 writes Right charge100.0f (`0x42C80000`);
- condition `SW_MTOB_XH` resolves to appended custom condition index512 and native apply returns success.

Thus the V2I diagnostic successfully applies the two source frame-13 activation events it intended to replay.

User result: this appears to affect the cells/substitution behavior only; it is not the complete intended Izanagi behavior.

Important source correction:
- `SPTYPE_ACTION10` has temporary native `ME_DMGHIT_OFF` / `ME_BODHIT_OFF` during activation;
- it turns body/damage hit back ON at frame14/15;
- therefore those activation hit-off events are not the one-minute Izanagi protection mechanism.

Do NOT implement a global or timed no-damage override based only on those events.

## 40.5 D-pad native consumer frontier

PC UltimateStormAPI source patch called “Dpad animations” changes a comparison from actor+0xE64 against0x7C to actor+0xF30 against1. The PC event236 opcode13 helper also writes actor+0xF30.

Switch original main independently contains a concrete F30 consumer in the resolved STATE137 controller family:

```
0x7E749C CMP W0,#1
0x7E74A0 B.NE 0x7E74CC
0x7E74A4 LDR W8,[X20,#0xF30]
0x7E74A8 CBZ W8,0x7E74CC
0x7E74AC LDR X8,[X20]
0x7E74B0 MOV X0,X20
0x7E74B4 LDR X8,[X8,#0xBA8]
0x7E74B8 BLR X8
0x7E74BC LDR X8,[X20]
0x7E74C0 MOV X0,X20
0x7E74C4 LDR X8,[X8,#0xBB8]
0x7E74C8 BLR X8
```

The uniquely resolved STATE137_CONTROLLER anchor is `main+0x7E6EA8`; the F30 LDR is exactly anchor+`0x5FC`.

V2J installs one read-only inline probe at the F30 LDR:
- derives address from resolver, no absolute fallback;
- verifies the exact 12-word native sequence;
- faithfully replays `LDR W8,[X20,#0xF30]` into W8;
- logs x19/x20 actor identities, F30, Right charge, E94/E98, and animation state;
- changes no branch, return value, condition, charge, hit flag, action, visibility, or damage policy.

Interpretation after hardware:
- if x20 is the custom actor and F30=1 after Right, then the native D-pad consumer is reached and the next frontier is the +0xBA8/+0xBB8 virtual family / downstream state it controls;
- if the custom actor never reaches this consumer, find the missing controller-route/admission boundary before it;
- if F30 is0, correlate which source event should enable it and why the existing opcode13 writes are not persistent at this boundary.

## 40.6 V2J source artifact

Package:
`NSC2Switch_RUNTIME_V2J_STAGE_NATIVE_POST_DPAD_CONSUMER_PROBE_DROPIN.zip`

SHA256:
`a10e72627497631f078a31fb2c054b4b9cdf8ed6fd830cb20220e896fb1b754d`

Verifier final marker:
`NSC_RUNTIME_V2J_SOURCE_VERIFY=PASS`

Verifier locks:
- original main SHA;
- reference P128 SHA;
- exact 30-word runtime delta;
- all seven original-main resolver signatures;
- safe opcode23 suppression;
- V2I activation-core diagnostic retained;
- opcode26 audio retained unchanged;
- exact native stage transition at0x48E344..0x48E364;
- restored PostStage/native member sweep call;
- exact native F30 consumer at0x7E749C..0x7E74C8;
- resolver-derived F30 probe installation;
- exact LDR replay into W8;
- no char281 gameplay branch;
- no global damage/visibility override.

Workflow artifact name:
`NSC-RUNTIME-V2J-stage-native-post-dpad-consumer-probe`

## 40.7 Minimal V2J hardware test

One fresh boot:
1. Right D-pad once;
2. observe whether only cells change or whether damage behavior changes;
3. let enemy land a normal hit/jutsu;
4. perform Tobi own UJ once;
5. observe whether Kamui still mixes with the original battle map;
6. save full log immediately.

Required markers:
- `[NSC:V2J] DPAD_NATIVE_READY installed=1 ... off=0x7e74a4 ...`;
- `[NSC:V2J] DPAD_NATIVE_CONSUMER ...` if the native F30 path is reached;
- `[NSC:V2J] STAGE2_SWITCH_NATIVE ... poststage=1 ...`;
- existing `[NSC:V2I] OP26_PLAY ...` as audio regression proof.

Do not change UJ admission, visibility policy, opcode17, or generic audio while testing V2J.

END OF R153 ADDENDUM

# R154 ADDENDUM — V2J BROAD REGRESSION / V2K RECOVERY BASELINE

## 41.1 New hardware inputs

V2J runtime artifact tested by user:
`NSC-RUNTIME-V2J-stage-native-post-dpad-consumer-probe.zip`

Artifact SHA256:
`3e2e33924589941490c1655044123aaf0fcbffa72c23c8718d33faf635d694db`

Deployed files verified from artifact:
- main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- subsdk9 SHA256 `f46bf29275392c79ddbdbbe3681abd2e3cc6aec32c5ecfe46b8b52650c2730dc`
- restore main SHA256 equals locked original main.

Hardware log:
`uzuy_log(32).txt`

Log SHA256:
`b04e8c1c6965b9a5f2f71218e8c38f10eaeeb20647095a4de56eafb9cceaab0f`

User verdict: V2J produces many regressions that are difficult to enumerate reliably. Treat V2J as gameplay FAIL; do not stack another behavioral patch on top of it.

## 41.2 Boot / architecture status

V2J boot itself is valid:
- seven resolver anchors resolve uniquely;
- `RESOLVER_READY resolved=7 total=7 fail_closed=1`;
- exact 30-word runtime delta applies;
- original main path is active;
- P128 UJ gate/session remains READY;
- no patch/resolver/fingerprint fatal marker appears.

Therefore the regressions are not explained by wrong main deployment or failed resolver startup.

## 41.3 What V2J actually exercised

V2J boot installed the added F30 consumer probe:
`[NSC:V2J] DPAD_NATIVE_READY installed=1 ... off=0x7e74a4 ...`

However the ENTIRE 10,770-line log contains:
- zero `[NSC:V2J] DPAD_NATIVE_CONSUMER` callbacks;
- zero `[NSC:V2I] IZANAGI_CORE_AB` markers;
- zero action77 / `SPTYPE_ACTION10` Right-activation fixture.

The only opcode17 marker in log32 writes Right charge 0.0f, not 100.0f. This run therefore does NOT provide a valid Right-D-pad Izanagi result and gives no useful evidence from the V2J F30 consumer hook.

The V2J stage mutation DID execute. Four `STAGE2_SWITCH_NATIVE` calls occur across two Tobi UJ cycles:
- `STG_2TOB_UNI_LT` twice;
- `STAGE_SI45A` twice.

Each executes:
`HandleStageChange -> Fix actor -> Fix enemy -> main+0x48E61C`
with `poststage=1`.

Opcode26 native SFX remains active in the same run. Audio had already been user-confirmed working in V2I and should remain frozen.

## 41.4 V2J causal rollback decision

Relative to V2I, V2J added only two meaningful runtime changes:

1. inline hook at `main+0x7E74A4` to read the native F30 consumer;
2. explicit `main+0x48E61C` call after custom StageMove handling.

The F30 hook produced zero runtime callbacks, so it supplied no frontier evidence while adding another trampoline/hook to a sensitive build. Remove it.

The explicit `0x48E61C` stage sweep executed four times and is the only V2J behavioral addition that is proven to have run during the problematic sequences. User reported broad regressions. Roll it back.

Do NOT change:
- P128 admission/session;
- opcode26 audio;
- visibility policy;
- original-main runtime delta;
- safe opcode23 suppression.

## 41.5 Static correction on main+0x48E61C

Fresh disassembly confirms `main+0x48E61C` is a no-argument routine that enumerates multiple battle members through `main+0x880150` and calls `main+0x77FBF4(member,1)` on those members and related `+0x1238` objects.

Thus the V2J call signature `void()` itself was not the obvious ABI error. The problem is more likely semantic/timing: invoking this whole native member sweep from the custom MovesetPlus StageMove bridge is not equivalent to the original PC helper and broad side effects are expected.

Do not call `0x48E61C` from the custom stage bridge again unless a later causal test establishes a required subset or exact surrounding native context.

## 41.6 V2K recovery baseline

New source package:
`NSC2Switch_RUNTIME_V2K_RECOVERY_PASSIVE_DPAD_DROPIN.zip`

SHA256:
`9ab34b28558998944e0d93696bd69d4b71a6ce40cb0a0ae46eb59d0c52a7afaa`

V2K starts from V2I, not V2J.

Behavior:
- no V2J F30 inline hook;
- no `main+0x48E61C` extra StageMove call;
- stage path restored to `HandleStageChange -> Fix actor -> Fix enemy`, `poststage=0`;
- V2I safe opcode23 suppression retained;
- V2I activation-core diagnostic retained;
- opcode26 audio retained unchanged;
- P128 unchanged;
- no force-visible;
- no global damage override;
- no force708/710;
- no char281 gameplay branch.

New passive marker at the existing V2I activation point:
`[NSC:V2K] DPAD_PASSIVE_SNAPSHOT`

It records:
- actor+0xF30 before/after;
- all four D-pad charge words before/after;
- E94/E98;
- animation state0x1268.

This adds reads/logging only and installs no new inline hook. The already-existing V2I diagnostic still performs its known condition + Right100 A/B; V2K adds no new gameplay write.

Stage recovery marker:
`[NSC:V2K] STAGE_SAFE_BASELINE ... v2j_poststage_removed=1 poststage=0 extra_stage_call=0`

Boot marker:
`[NSC:V2K] READY recovery_baseline=V2I v2j_stage_post=0 v2j_dpad_inline_hook=0 ...`

Verifier final marker:
`NSC_RUNTIME_V2K_SOURCE_VERIFY=PASS`

## 41.7 Shutdown assertion

At the very end of log32, after configuration writes, Oboe stream destruction, NVDRV unpin warning and pipeline-cache serialization, Uzuy prints `host_memory.cpp Assertion Failed!` and reinitializes frontend graphics.

As in earlier runs, treat this as shutdown/emulator behavior unless reproduced during active gameplay. It is not used as the root cause of the V2J gameplay regressions.

## 41.8 Next hardware test

Use V2K only. Minimal fresh-boot test:
1. enter battle and verify basic movement/hits first;
2. Right D-pad exactly once;
3. observe whether Tobi remains visible and what cells/substitution do;
4. let enemy land one normal hit and one jutsu;
5. use Tobi UJ once;
6. note whether audio remains present and whether battle map still mixes with Kamui;
7. save full log immediately.

Required markers:
- `[NSC:V2K] READY ...`;
- `[NSC:V2K] DPAD_PASSIVE_SNAPSHOT ...` if Right activation reaches action77/SPTYPE_ACTION10;
- `[NSC:V2K] STAGE_SAFE_BASELINE ... poststage=0 ...` during Tobi UJ;
- existing `[NSC:V2I] OP26_PLAY ...` for audio regression proof.

If V2K restores general stability, V2J is permanently rejected and future work resumes from V2I/V2K only.

END OF R154 ADDENDUM

## R155 CORRECTION — AUDIO STATUS SPLIT (2026-09-27)

User correction after V2J/V2K discussion: Tobi UJ does NOT have Tobi's own dialogue/voice. Only generic UJ sound effects are audible.

This corrects earlier shorthand that called “UJ audio” PASS.

Locked interpretation:
- Event236 opcode26 generic SFX path: PASS/partially restored. V2I/V2J logs show OP26_PLAY for S_PL_etc_l, S_PL_DMG_cmn_vS_rv, S_PL_etc_m.
- Character-specific Tobi voice/dialogue: NOT FIXED.
- Source PRM explicitly contains Event150 cues mtob_ougi_001, mtob_ougi_002, mtob_ougi_003, plus other Tobi-specific cues.
- Current V2J log contains no Event150 / mtob_ougi / VOICE trace because runtime has no Event150 tracer/registration port yet.
- Historical audit identified two separate layers: Event150 cue dispatch and Character Sound Entries / Character Sound ACB registration. Do not conflate either with opcode26 SFX.
- V2K recovery build intentionally does not add voice changes. It remains focused on reverting V2J regressions while preserving proven opcode26 SFX.

Next safe audio frontier after gameplay recovery is stable:
1. add READ-ONLY Event150 tracer for custom actor;
2. capture cue string and callback result;
3. trace custom Character Sound Entry / ACB lookup for custom IDs;
4. if lookup misses, port registration; if lookup succeeds but silent, inspect ACB/AWB cue payload.

Do NOT modify P128 UJ admission for this issue.

---

# 37. R156 — V2K HARDWARE AUDIT / LOG33

Date: 2026-09-27
Input runtime artifact: NSC-RUNTIME-V2K-recovery-passive-dpad.zip
Input log: uzuy_log(33).txt

## Artifact integrity
- Artifact ZIP SHA256: `6e1035ec1dbd6785b10d68d5b61294217ec2af6c22eeca271058a357fe6159ce`
- Deployed main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- Deployed V2K subsdk9 SHA256: `c96febd8b78ea8d15759480a7a3a41e67e7612d34ee7f64387c6fb64b0108f87`
- main is exact original v1.70 main.

## V2K infrastructure result
- Resolver 7/7 PASS.
- Runtime patch 30 words PASS.
- V2J stage-post call removed.
- V2J F30 inline hook removed.
- No damage override.
- No force-visible.
- No char281 final branch.

## UJ result
- P128 admission remains healthy: custom raw15 reaches session and action710.
- `STG_2TOB_UNI_LT` request executes and stage ID changes to `0x01D1CA7E`.
- Stage returns to `STAGE_SI45A` / `0x2BCB5498` on exit.
- V2K uses V2I safe stage baseline: actor+enemy position fix, no extra post-stage sweep.
- Generic UJ SFX path remains active via opcode26/native actor vtable +0x1030.
- Voice/dialogue is still unresolved. There is no Event150 tracer in V2K, so absence of `mtob_ougi_*` strings in log33 is not proof Event150 does not execute; it only confirms V2K does not observe or port that path.

## Right D-pad result
Two Right activation attempts are visible.
Each attempt:
- action928 receives opcode23 p3=77 / `SPTYPE_ACTION10`;
- full PL_ANM930 remains suppressed;
- `SW_MTOB_XH` resolves to condition index512 and apply returns 1;
- Right charge at actor+0x12B84 becomes/retains `100.0f` (`0x42C80000`);
- actor+0xF30 is already 1 before activation and remains 1 after activation;
- animation state remains 928 during the synthetic frame13 activation core.

Important correction:
- `actor+0xF30 == 1` is NOT evidence that Right activation itself succeeded; it was already 1 before the write. Retire F30 as a Right-activation flag.

## Missing SPTYPE_ACTION10 semantics
The source section `PL_ANM_SPTYPE_ACTION10` contains important native events that V2K does not replay because full animation930 is suppressed:
- frame0: 159 `ME_ANM_SPEED_SET`; 33 `ME_FWDVELOCITY_SET`
- frame10: 298 `ME_NOT_NOMALCOMBO_CAMERA_DIST`
- frame11: 186 `ME_DMGHIT_OFF`; 184 `ME_BODHIT_OFF`; 32 `ME_JUMPVEL_SET`; 41 `ME_FLIGHT_BEGIN`
- frame12: 159/186/41 updates
- frame13: 186; Event121 `SW_MTOB_XH`; opcode17 Right=100; 254 `ME_MOT_UPGRADE_CANCEL`
- frame14: 42 `ME_FLIGHT_END`; 36 `ME_WARP_AROUND_ENEMY`; 299 camera reset; 186; 183 `ME_BODHIT_ON`
- frame15: 185 `ME_DMGHIT_ON`
- frame19: 119 `ME_ACT_FALL`

This explains why the current synthetic "frame13-only" activation is incomplete. It proves V2K skips source-authored hit/body disable/enable and motion/warp lifecycle around activation. Do not replace this with a global invulnerability hack.

## New frontier
1. Keep V2K as stable recovery baseline.
2. Build a READ-ONLY Event150 tracer for Tobi voice before changing ACB/sound registration.
3. For Right D-pad, stop using F30 as success signal.
4. Trace/port the exact `SPTYPE_ACTION10` native event subset safely and generically, beginning with event186/184/183/185 semantics and condition lifetime, without calling full animation930 and without global damage/visibility overrides.
5. UJ stage visual mixture remains a separate environment-ownership issue; V2K proves stage ID transitions work but does not prove battle-map geometry unloads.


# R157 — PRIORITY REORDER + ULTIMATESTORMAPI PORT MATRIX

Date: 2026-09-28

User-directed priority change:
1. UJ stage/environment parity FIRST.
2. Voice/Event150 after stage unless stage work needs audio-independent validation.
3. D-pad/Izanagi work PAUSED until UJ stage mixture is resolved or sharply isolated.

## UJ stage current proof
- P128 admission/session is solved and must remain untouched.
- Event236 op2 emits STG_2TOB_UNI_LT.
- V2K StageMove helper resolves the custom stage and live stage ID changes to 0x01D1CA7E.
- On UJ exit, stage returns to STAGE_SI45A / 0x2BCB5498.
- V2K matches the inspected PC UltimateStormAPI helper order: specific/default StageMove handler -> HandleStageChange -> FixCharPosition(actor) -> FixCharPosition(enemy).
- Despite this, battle-map geometry remains mixed with the Kamui environment.
- Therefore the active frontier is no longer stage-name lookup or stage-ID mutation. It is custom-stage registration/resource binding and environment/geometry ownership/lifecycle on Switch.
- V2J's extra main+0x48E61C sweep is rejected; it caused broad regressions and is not in the PC helper.

## Tobi custom stage package audit
The packaged stage contains:
- Stages/STG_2TOB_UNI_LT/data/stage/StageInfo.bin.xfbin
- stage_config.ini: Game=NSC, BGM_ID=-1, BGM_ID_NS4=-1, Hell=false
StageInfo strings include:
- STG_2TOB_UNI_LT
- c_sta_11
- BTL_NS4_si45a
- data/spc/mtobspl3_e.xfbin
- data/stage/sd_decal_type01.xfbin
- data/stage/lensFlare/oprism_lensFlare.xfbin
This proves the authored stage has resource bindings beyond a CRC/stage ID. Current runtime proof does not yet establish that these environment resources replace/unload the old battle-stage nodes correctly on Switch.

## UltimateStormAPI / ModdingAPI port status at R157

### Working / proven or reusable
- RuntimeResolver / fail-closed pattern validation.
- RuntimePatcher on original v1.70 main; exact 30-word condition/P67/P128 delta.
- CPK bind hook / custom content delivery.
- Custom characode lookup for IDs above vanilla max; Tobi ID281 -> mtob works.
- Condition descriptor extension: native512 + generated5 = 517 for current fixture.
- Event121 SELF custom condition apply path.
- Event236 custom dispatcher framework.
- Event236 op2 StageMove: stage lookup/ID transition + actor/enemy position fix; environment parity still partial.
- Event236 op3 change skill.
- Event236 op4 change speed.
- Event236 op8 walk speed.
- Event236 op13 D-pad animation field write.
- Event236 op14/op15 selector1 UJ semantic bridge only; not full generic control selector parity.
- Event236 op17 D-pad charge source-parity.
- Event236 op26 generic SFX playback via native Switch actor vtable+0x1030.
- PlayAction / central animation setter instrumentation.
- P128 custom UJ admission/session compatibility; natural 707->710 path, victim safety and Naruto UJ regression-safe.
- Victim-safe compatibility shadows for dangerous custom Event236 semantics.

### Partial / intentionally incomplete
- ConditionRegistry is generated/fixed for current 5 extra conditions; not yet fully dynamic like PC API architecture.
- SpecialCondParam behavior is not a complete generic PC-source port; donor57 mapping experiments are retired.
- Event236 op12 visibility is shadowed for safety, not full source parity.
- Event236 op14/op15 generic control selectors other than selector1 are not ported.
- Event236 op22 PL_ANM path is not fully source-faithful/validated.
- Event236 op23 play_action is deliberately safety-suppressed for Tobi SPTYPE_ACTION10 because full PL_ANM930 causes disappearance.
- StageMove op2 changes stage state correctly but environment/geometry resource lifecycle is incomplete.
- OugiAwakeningParam / awakening semantics are incomplete.
- SoundManager is partial: generic opcode26 SFX works, character voice registration does not.

### Not ported / not proven
MovesetPlus opcodes:
- 1 BGM
- 5 timed speed
- 6 blur
- 7 FOV
- 9 jump height
- 10 SetPlayerParam
- 11 ChangePlayerParam
- 16 timed control
- 18 gray/screen color effect
- 19 HUD control
- 20 IA scene
- 21 camera algorithm
- 24 face animation
- 25 timed face animation
- 27 projectile deflection enable
- 28 projectile deflection disable
- 29 projectile takeover

Character/audio expansion:
- Event150 character voice path/tracer/playback
- Character Sound Entries expansion
- Character Sound ACB expansion
- mtob_ougi_001/002/003 voice playback

UltimateStormAPI managers/features not yet ported as reusable Switch subsystems:
- BGMManager/BGMExpander
- TeamUltimateJutsuManager / pairSpSkillManagerParam
- ProjectileManager / projectile deflection hooks
- PartnerSlotParam generic partner expansion
- CharRelationExpander
- SusanooCondParam
- SpecialInteractionManager
- GudoBallParam
- GuardEffectParam
- full OugiAwakeningParam logic
- SceneExpander / IA scene system
- Lua script integration
- Jutsu Selector UI/input subsystem
- restored Tilt/Chakra-Shuriken CtrlInputPad compatibility as a generic feature
- costume/color expansion
- wall-run compatibility extensions
- editor/camera/debug UI functionality
- PC plugin DLL loader semantics (not a Switch runtime goal; authoring stays PC-side)

## Stage-first next technical plan
1. Keep V2K gameplay baseline; freeze D-pad and opcode26.
2. Trace the native stage/environment object graph immediately before STG_2TOB_UNI_LT, after StageMove handler, after HandleStageChange, and on STAGE_SI45A restore.
3. Identify which pointers/resources represent old battle geometry versus the custom stage environment.
4. Trace native stage transitions that genuinely replace environments and compare their teardown/rebind sequence with the custom Event236 path.
5. Verify the custom StageInfo resource bindings (c_sta_11 / BTL_NS4_si45a / mtobspl3_e) are present in the live stage object, not merely registered in the stage table.
6. Only after a missing lifecycle call/resource binding is proven, add one narrow stage-only A/B. Do not reintroduce V2J main+0x48E61C sweep.


---

# R158 — V2L STAGE-ONLY RESOURCE / ENVIRONMENT TRACE

Date: 2026-09-28

User priority remains locked:
1. UJ stage/environment parity first.
2. Voice/Event150 later.
3. D-pad/Izanagi paused.

## Baseline
V2L is derived from V2K and does not change gameplay semantics:
- P128 admission/session unchanged.
- Event236 op2 StageMove sequence unchanged: specific/default -> HandleStageChange -> Fix actor -> Fix enemy.
- V2J manual `main+0x48E61C` PostStage call remains removed.
- opcode26 generic SFX unchanged.
- D-pad code unchanged.
- Event150/voice untouched.
- no damage/visibility override.
- no char281 gameplay branch.

## Why V2L exists
R157 proof already narrowed the stage bug:
- `STG_2TOB_UNI_LT` is received.
- stage CRC `0x01D1CA7E` is accepted.
- live stage ID changes to that value.
- stage returns to `STAGE_SI45A` afterward.
- battle-map geometry still remains mixed with the Kamui cinematic.

Therefore V2L observes the resource/environment boundary rather than modifying stage behavior.

## V2L read-only instrumentation
### Stage object graph snapshots
Marker:
`[NSC:V2L] STAGE_GRAPH`

Captured at:
- `pre_specific`
- `post_specific`
- `post_handle`
- `post_fix`

Objects recorded:
- stage global
- stage manager
- `StageMove` object
- object inner
- stage context
- stage-state global / state
- live stage ID
- selected raw pointer-sized fields for before/after comparison

No pointer is rewritten.

### Stage asset trace window
Markers:
- `[NSC:V2L] STAGE_TRACE_ARM`
- `[NSC:V2L] STAGE_TRACE_DISARM`

The first custom Event236 StageMove arms the asynchronous resource trace. It stays active through the next StageMove so resources loaded during the cinematic are observable. The second StageMove disarms it after the restore path.

### Resource load boundaries
Read-only hooks installed for:
- native file-load request function
- native file-open function

Existing markers become active for stage-relevant paths:
- `[NSC:P50A] LOAD_REQUEST ... path=... result=...`
- `[NSC:P50A] FILE_OPEN ... path=... result=...`

Always-interesting stage tokens include:
- `mtobspl`
- `2tob`
- `c_sta_11`
- `STG_2TOB`

During the active trace window, XFBIN/stage paths are traced more broadly to catch asynchronous resource loads.

### Native stage lifecycle observation
Read-only trampolines are installed for:
- `HandleStageChange`
- `PostStage` (`main+0x48E61C`)

Important:
- V2L DOES NOT call PostStage.
- It only logs if the game itself calls it.
- This avoids repeating V2J's broad-regression experiment.

## Decision tree after V2L hardware log
A. Kamui resources never requested:
- frontier = custom StageInfo/resource-registration or StageMove->resource-load handoff.

B. Resources requested but FILE_OPEN result=0:
- frontier = CPK/path/packaging/bind resolution.

C. Resources open successfully but stage graph remains bound to old environment:
- frontier = environment teardown/rebind lifecycle.

D. Graph rebinds and resources open, but battle geometry still persists:
- frontier = render-node visibility / scene ownership, not stage lookup.

E. Native PostStage appears automatically:
- inspect native timing/caller and compare; do not force-call it.

F. Native PostStage never appears:
- no evidence it belongs in the source-faithful StageMove path; keep V2J sweep rejected.

## V2L source verification
Local source verifier passes:
- resolver signatures unique on original main
- exact original-main hash
- exact 30-word runtime patch reference delta
- V2K baseline retained
- no manual PostStage call
- stage graph marker present
- file request/open trace present
- HandleStageChange/PostStage observation-only hooks present
- D-pad/voice/P128 unchanged

Package:
`NSC2Switch_RUNTIME_V2L_STAGE_RESOURCE_ENV_TRACE_DROPIN.zip`

Package SHA256:
`dce5f2ec511820f1608903e8dd0601c59bae214c47b65e15756231bf55ccc621`

GitHub Actions artifact name after successful build:
`NSC-RUNTIME-V2L-stage-resource-environment-trace`

## Required hardware test
Use a fresh boot. Do not test D-pad in this run.
1. Select Tobi.
2. Use Tobi UJ once.
3. Let the full cinematic and return-to-battle sequence finish.
4. Save the full log immediately.

Primary markers to inspect next:
- `V2L READY`
- `STAGE_TRACE_ARM`
- four `STAGE_GRAPH` phases for `STG_2TOB_UNI_LT`
- `LOAD_REQUEST` / `FILE_OPEN` during the active trace
- any native `POST_STAGE`
- four `STAGE_GRAPH` phases for the restore StageMove
- `STAGE_TRACE_DISARM`

---

# R159 — V2L RETIRED BEFORE HARDWARE; V2M SAFE STAGE TRACE

Date: 2026-09-28

## Correction
V2L is RETIRED before hardware testing. Static re-audit found an unnecessary risk:
- V2L captured stage-manager/object/context pointers before the stage transition;
- after `HandleStageChange`, it reused those old pointers and dereferenced raw fields for logging;
- a stage transition may replace or release those objects, so post-transition dereference of pre-transition pointers is not acceptable diagnostic hygiene.

No V2L hardware result should be collected. Use V2M instead.

## V2M baseline
V2M is rebuilt directly from V2K, not from V2L.
Gameplay behavior stays identical to V2K:
- original main + V2D runtime resolver/patcher
- exact 30-word proven runtime delta
- P128 UJ admission/session unchanged
- Event236 op2 remains specific/default -> HandleStageChange -> Fix actor -> Fix enemy
- V2J manual PostStage call remains removed
- opcode26 generic SFX unchanged
- D-pad behavior unchanged
- Event150/character voice untouched
- no damage override
- no visibility override
- no char281 gameplay branch

## V2M safe stage graph tracer
V2M re-resolves the known stage graph from the proven globals independently at every phase:
- pre_specific
- post_specific
- post_handle
- post_fix

Marker:
`[NSC:V2M] STAGE_GRAPH ... fresh_resolve=1 stale_pointer_deref=0 readonly=1`

Logged identities only:
- stage global
- manager
- StageMove object
- object inner
- stage context
- stage-state global
- stage-state object
- stage ID

V2M does not dump arbitrary fields through stale pointers.

## Resource trace
Diagnostic pass-through hooks only:
- FileLoadRequest
- FileOpen
- HandleStageChange
- PostStage observation

Existing loader markers:
- `[NSC:P50A] LOAD_REQ ...`
- `[NSC:P50A] FILE_OPEN ...`

PostStage is observation-only. V2M never invokes it manually.

The first custom StageMove opens the resource window. The second normally closes it. Failure paths explicitly disarm the window to prevent accidental broad tracing after a failed transition.

## Verification
Local source verifier PASS:
- V2K baseline retained
- V2M main/header install path present
- fresh graph re-resolution present
- V2L stale-field logger absent
- all four stage phases present
- load request/open hooks present
- HandleStageChange/PostStage pass-through hooks present
- manual PostStage call absent
- opcode23 safe suppression retained
- opcode26 retained
- P128 retained
- workflow deploys original main
- original main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- P128 reference SHA256 `904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff`
- decompressed text delta exactly 30 words

Package:
`NSC2Switch_RUNTIME_V2M_STAGE_SAFE_RESOURCE_ENV_TRACE_DROPIN.zip`

Package SHA256:
`50d8cca3d4debee3070af5ee9570d6c46d767b10c31f41b6a4a475c5fb7d392c`

GitHub Actions artifact name:
`NSC-RUNTIME-V2M-stage-safe-resource-environment-trace`

## Required hardware test
1. Fresh boot.
2. Select Tobi.
3. Do NOT press D-pad.
4. Use Tobi UJ once.
5. Let cinematic finish and return to battle.
6. Save full log immediately.

Inspect next:
- `V2M READY`
- `STAGE_TRACE_ARM`
- `STAGE_GRAPH` x4 for `STG_2TOB_UNI_LT`
- `LOAD_REQ` / `FILE_OPEN` during cinematic
- native `POST_STAGE` if any
- `STAGE_GRAPH` x4 for restore stage
- `STAGE_TRACE_DISARM`

Priority remains:
1. UJ stage/environment parity
2. Tobi Event150 voice
3. D-pad/Izanagi

---

# R160 — V2M HARDWARE RESULT + NATIVE STAGE REGISTRY FRONTIER + V2N

## Hardware input
User tested compiled V2M and reports:
- Tobi UJ cinematic still mixes with the battle map.
- Tobi character voice/dialog is still absent; only generic UJ effects are heard.

Files:
- `uzuy_log(34).txt`
  - SHA256 `0912a10e1d369ca077bb1105aa187bb7415153780b7e51db864c4cebcf70bc33`
- `NSC-RUNTIME-V2M-stage-safe-resource-environment-trace.zip`
  - SHA256 `a670c8fd29b64d75b767f53c9f97d21da105aad5626812c4044646a882126efa`
  - deployed main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
  - V2M subsdk9 SHA256 `b0c87b383124a0f1473bd776d302ad40e412576169c1e03e40c1f680188e44ec`

## V2M result — stage request is numeric only at current runtime boundary
V2M boot is correct and diagnostics are read-only.

Custom UJ entry:
- `STG_2TOB_UNI_LT` reaches Event236 opcode2.
- pre-specific live stage = `2759012590`.
- post-specific live stage = `30526078` = `0x01D1CA7E`.
- HandleStageChange runs and returns with the same ID.
- stage graph identity remains unchanged across:
  - pre_specific
  - post_specific
  - post_handle
  - post_fix
- no stage resource LOAD_REQ/FILE_OPEN appears while the Kamui stage trace window is active.

UJ exit:
- `STAGE_SI45A` changes live ID to `734745752` = `0x2BCB5498`.
- HandleStageChange runs.
- graph identity again remains unchanged.

This retires these root candidates:
- StageMove text missing
- CRC wrong
- stage ID write missing
- HandleStageChange not called
- FixCharPosition not called

It does NOT prove the custom stage descriptor/environment is registered.

## Voice correction from V2M
The custom voice assets are physically delivered successfully:
- `disc:data/sound/Voice/JP/mtob_pl.xfbin` FILE_OPEN result=1
- `disc:data/sound/SndEvent/mtob_ev.xfbin` FILE_OPEN result=1
- `disc:data/sound/SndEvent/mtob_ev_spl.xfbin` FILE_OPEN result=1

Therefore missing `mtob_ougi_001/002/003` is not a missing-file problem. Event150 / Character Sound Entries / ACB runtime dispatch remains unresolved, but voice stays frozen until stage is fixed.

## Native Switch StageSpecific back-slice — new decisive static boundary
Original v1.70 main:
- wrapper `main+0x535F88`
- transition worker `main+0x535FBC`

Worker sequence:
- `main+0x53605C`: store requested stage ID into live state.
- `main+0x536074`: `LDR X8,[X26,#0x6C10]`
- `main+0x53607C`: `LDR X0,[X8,#0x148]`
- `main+0x536080`: `BL main+0x8364F8` with W1=requested stage ID.
- `main+0x536084`: `CBZ X0, main+0x536378`.

Thus a null descriptor lookup skips the main descriptor/environment setup block despite the numeric stage ID already having changed.

`main+0x8364F8` is a uint32-keyed tree lookup. Exact first 8 words:
- F8408C09
- B40001A9
- AA0003E8
- B940212A
- 6B01015F
- 1A9F27EA
- 9A893108
- F86A5929

On success it returns node payload at +0x28; on failure it returns null.

Additional StageInfo manager evidence:
- `main+0x835FCC` loads `data/stage/StageInfo.bin.xfbin`, chunk `stageInfo`.
- `main+0x835FF0` loads `data/stage/AdvStageInfo.bin.xfbin`.
- successful StageSpecific descriptor path later references `data/stage/stageFilter.xfbin`.

## Tobi package stage metadata
The `.unse` contains:
- `Stages/STG_2TOB_UNI_LT/data/stage/StageInfo.bin.xfbin`
- `stage_config.ini` with `Game=NSC`, BGM IDs -1.
- StageInfo strings:
  - STG_2TOB_UNI_LT
  - c_sta_11
  - BTL_NS4_si45a
  - data/spc/mtobspl3_e.xfbin
  - decal/lens-flare resources

It does NOT contain its own `stageFilter.xfbin` or `AdvStageInfo.bin.xfbin`.
Historical Alpha7 compiler evidence proved only static StageInfo 181->182 merge; complete stage runtime registration/environment integration was not proven.

## Current strongest hypothesis
The current custom StageMove can write the custom CRC into stage state, but the native runtime descriptor registry may not contain that CRC. If so, StageSpecific takes the `CBZ` miss path, never rebinds the stage environment, and the old battle-map geometry remains visible. This exactly matches V2M hardware behavior, but requires runtime proof before any mutation.

## V2N — Stage Registry Proof
Created from V2M/V2K baseline.

Purpose:
- duplicate the exact native stage registry lookup read-only immediately before and after StageSpecific.

Pointer chain from original main:
- runtime root = `*(base+0x2143488)`
- registry owner = `*(root+0x6C10)`
- registry map = `*(owner+0x148)`
- descriptor = `main+0x8364F8(map, stage_id)`

Marker:
`[NSC:V2N] STAGE_REGISTRY phase=... text=... key=... result=... found=0/1 readonly_lookup=1 insert=0 mutation=0`

Interpretation:
- custom `STG_2TOB_UNI_LT found=0`, vanilla restore `STAGE_SI45A found=1` => missing custom runtime stage registration PROVEN.
- both found=1 => move downstream into descriptor contents / stageFilter / environment setup.
- both found=0 => re-audit pointer-chain assumption; do not mutate.

V2N makes NO gameplay mutation:
- no registry insert
- no descriptor clone
- no manual PostStage
- no D-pad changes
- no voice changes
- no P128 changes
- no char281 gameplay branch

Source verifier PASS including original-main hash, P128 reference, and exact 30-word delta.

Package:
`NSC2Switch_RUNTIME_V2N_STAGE_REGISTRY_PROOF_DROPIN.zip`
SHA256 `77138b1675d3ffda268fb616fbadc3f925f6a011ca0810e586c425d1648f73d4`

GitHub Actions artifact name:
`NSC-RUNTIME-V2N-stage-registry-proof`

## Locked priority after R160
1. Stage registry proof/fix.
2. Stage descriptor / stageFilter / environment rebind if registry is present.
3. Event150 Tobi voice.
4. D-pad/Izanagi.

---

# R161 — V2N HARDWARE PROOF: CUSTOM STAGE REGISTRY MISS + V2O NATIVE REINDEX A/B

Date: 2026-09-28

## Hardware input
User supplied:
- `uzuy_log(35).txt`
  - SHA256 `453f095c4c61929a6317e7bf492258de1a202e01a1dc1e3556b42fb262345245`
- `NSC-RUNTIME-V2N-stage-registry-proof.zip`
  - SHA256 `7ef6e194d062c66ca231dc57fe7a130e74a5f666c4fd79106a4273795289e9a2`
  - deployed main remains original SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
  - deployed V2N subsdk9 SHA256 `f2b4e7fc503c179d363a83833bfd13067e9e049cdff773e878d33cc5821bf0bd`

## V2N decisive result
Custom UJ stage request:
- `STG_2TOB_UNI_LT`, key `0x01D1CA7E`.
- registry pre_specific: `result=0x0 found=0`.
- registry post_specific: `result=0x0 found=0`.

Vanilla restore stage:
- `STAGE_SI45A`, key `0x2BCB5498`.
- registry pre_specific: `result=0x3aba70e080 found=1`.
- registry post_specific: same descriptor / `found=1`.

Live chain in that run:
- runtime root `0x1a297a9710`
- registry owner `0x3ab5ca3270`
- StageInfo manager / registry object `0x3ab8f01960`

This proves the V2N pointer chain is valid and retires the earlier hypothesis status:
**missing custom runtime stage registration is now PROVEN.**

Consequences:
- custom StageMove text is correct;
- CRC is correct;
- live stage ID mutation works;
- StageSpecific is called;
- but StageSpecific cannot reach its descriptor/environment setup branch because the custom key is absent from the native StageInfo registry.
- vanilla restore hits the same registry successfully, validating the lookup path.

## CPK / resource delivery remains healthy
The same run shows:
- `Tobi_Switch.cpk` bind returns success with priority 32.
- Tobi sound files load/open successfully.
Therefore the stage fix should target registration/StageInfo ingestion before touching CPK binding or UJ admission.

## New static proof — reuse native StageInfo loader, do not hand-build descriptors
Original Switch v1.70 main links StageSpecific and StageInfo initialization to the same +0x148 object.

StageSpecific:
- `main+0x536074`: owner = `[runtime_root+0x6C10]`
- `main+0x53607C`: X0 = `[owner+0x148]`
- `main+0x536080`: lookup `main+0x8364F8(X0, stage_id)`

Native manager initialization:
- `main+0x406490`: X0 = `[manager_collection+0x148]`
- `main+0x406498`: `BL main+0x835FAC`

`main+0x835FAC` is the native StageInfo loader. It:
- requests `data/stage/StageInfo.bin.xfbin`;
- parses chunk `stageInfo` through `main+0x836010 / 0x8360C8`;
- also requests `data/stage/AdvStageInfo.bin.xfbin`;
- parses 0x130-byte source records;
- allocates 0x180-byte runtime descriptors;
- populates descriptors with native helpers;
- computes the native key/hash;
- inserts with native tree function `main+0x836708`;
- handles duplicate keys natively.

Exact `main+0x835FAC` first 12 words verified against original main:
`F81E0FFE A9014FF4 D000C874 F942F294 AA0003F3 F0008E21 9128CC21 AA1403E0 942746DB AA0003E1 90009502 912F1C42`.

## V2O — Native StageInfo Reindex on Registry Miss
Built from V2N/V2K baseline.

Generic trigger:
- Event236 opcode2 requests a specific stage key;
- native registry lookup misses;
- extra mod CPK has already bound successfully;
- exact v1.70 StageInfo loader fingerprint passes;
- reload has not already been attempted this session.

Controlled action:
1. Resolve the already-live native StageInfo manager from the exact StageSpecific chain.
2. Call native `main+0x835FAC(stage_manager)` ONCE.
3. Let the game's own parser/descriptor builder/tree insertion handle StageInfo records and duplicate vanilla entries.
4. Re-probe the requested key.
5. Continue normal StageSpecific.

Marker:
`[NSC:V2O] STAGE_REINDEX text=... key=... before_found=0 after_found=0/1 ...`

Decision:
- `after_found=1`: native reindex repaired registration; inspect whether Kamui environment/resource requests now appear and whether battle-map mixture is gone.
- `after_found=0`: mounted CPK does not expose a usable custom StageInfo record to the native loader; next fix is PC-side StageInfo packaging/semantic merge, NOT more runtime lifecycle calls.

Safety constraints retained:
- no manual descriptor clone/build;
- no manual tree insertion;
- no manual PostStage;
- no D-pad change;
- no voice change;
- no P128 change;
- no char281 gameplay branch;
- no global visibility/damage override;
- reload only once per session and only after a real registry miss after successful custom CPK bind.

Source verifier PASS:
- original main hash exact;
- reference P128 hash exact;
- runtime reference delta exact 30 words;
- V2K/V2M/V2N baselines retained;
- V2O native-loader fingerprint present;
- workflow packages original main.

Package:
`NSC2Switch_RUNTIME_V2O_NATIVE_STAGE_REINDEX_DROPIN.zip`
SHA256 `d19a4fb1af61027a45bd9232feec726324ada27f019f4d9445db5372005f5501`

GitHub Actions artifact name:
`NSC-RUNTIME-V2O-native-stage-reindex`

## Locked priority after R161
1. Test V2O native StageInfo reindex and inspect `after_found` + visual Kamui stage.
2. If registration succeeds but map still mixes, inspect the now-active native environment setup/resource path downstream of descriptor hit.
3. If registration remains missing, fix StageInfo packaging/semantic merge PC-side.
4. After UJ stage is correct: Event150 Tobi voice.
5. D-pad/Izanagi last.
