# NSC2Switch MASTER CHECKPOINT — 2026-10-04 R206 FULL

## CURRENT FRONTIER — R204B NATIVE-ID MTOB TRACE VALID; `mtobprm_load` LOADS, `mtobcharsel` OPENS BUT DOES NOT COMPLETE; R204C PROCESS OFFSET FIX READY

### R206 hardware/runtime result
User hardware report on the R203A native-Naruto `1nrt -> mtob` carrier with the R204B read-only tracer:

- `NARUTO_PREVIEW=EMPTY`
- R204B tracer startup: `installed=1`
- R204B PROCESS tracer: `process_optional_installed=0`
- no gameplay/main/ID/path rewrite policy was installed by the tracer.

This is a valid runtime trace for the mandatory R204B loader hooks, but R204B lacked its post-open PROCESS observation due to a source offset typo.

### R204B trace — locked facts
Startup:

```text
[NSC:P50A] fingerprint FAIL R204B_PROCESS_OPTIONAL off=0x106f404 word0=97fe40a7
[NSC:R204B] READY installed=1 process_optional_installed=0 ...
```

Parent manifest:

```text
data/spcload/mtobprm_load.bin.xfbin
  LOAD_CREATE -> non-null
  LOAD_REQ -> non-null
  FILE_OPEN sim:data/spcload/mtobprm_load.bin.xfbin result=1
  LOAD_STATUS -> status=2
```

Therefore the new `mtob` parent prm_load remains proven visible and successfully loaded in the clean native-ID46 carrier path.

Character-select preview XFBIN:

```text
data/ui/max/crsel/c/mtobcharsel.xfbin
  LOAD_CREATE -> non-null
  LOAD_REQ -> non-null
  FILE_OPEN result=1
  later LOAD_CREATE/LOAD_REQ again
  FILE_OPEN result=1 again
  later LOAD_REQ again
```

No `LOAD_STATUS` transition for `mtobcharsel.xfbin` was captured before shutdown, and no R204B `CHUNK` line was emitted for `mtob` in this run.

### New strongest interpretation
The preview blocker is now downstream of path visibility/file open for `mtobcharsel.xfbin`.

Do NOT classify this as:
- `sound.cpk` carrier failure;
- parent `mtobprm_load` registration failure;
- numeric ID46/281 range failure;
- missing `mtobcharsel` path;
- simple file-open failure.

`mtobcharsel.xfbin` is found and opened successfully, but the observed run does not show it reaching a completed load state. The next valid boundary is the native post-open XFBIN PROCESS/read path.

### R204B PROCESS hook bug — exact source typo found
R204B source declared:

```text
kLoadRequestProcessOffset = 0x106F404
```

The clean v1.70 decompressed `main` instead contains the exact intended 8-word PROCESS fingerprint uniquely at:

```text
main+0x116F404
A9BC7BFD A9015FF8 A90257F6 A9034FF4
D10A03FF D0019008 B9807058 AA0003F5
```

The old `main+0x106F404` contains `0x97FE40A7` as its first word, exactly matching the R204B runtime fingerprint failure.

This is a diagnostic-source offset typo, not evidence against the game architecture.

### R204C — next diagnostic build
R204C fixes only the PROCESS tracer boundary:

```text
0x106F404 -> 0x116F404
```

R204C remains read-only and installs no:
- game `main` override;
- CPK binder;
- numeric-ID expansion/alias;
- path rewrite;
- forced load status;
- return override;
- gameplay patch.

R204C now treats PROCESS as mandatory together with:
- LOAD_REQ
- LOAD_CREATE
- LOAD_STATUS
- FILE_OPEN
- PROCESS
- CHUNK

Expected startup acceptance marker:

```text
[NSC:R204C] READY installed=1 process_installed=1 ...
```

If PROCESS reports `status=5` and/or nonzero `readerr` for `mtobcharsel`, the failure is inside native XFBIN post-open processing/read. If PROCESS succeeds but no preview appears, continue to CHUNK/internal-key or downstream actor/model construction based on the trace; do not add more assets blindly.

### Packaging discipline added by user
All future GitHub source-kit ZIPs for this branch must be **flat-root archives**:

- extracting directly into the repository root must produce `.github/`, `overlay/`, `prepare_exlaunch.sh`, verifier/analyzer files, etc.;
- no wrapping top-level source directory is allowed;
- transient `__pycache__` / `*.pyc` files must not be shipped.

### R206 status

```text
R204B_HARDWARE_PREVIEW=EMPTY
R204B_TRACE_INSTALL=PASS
R204B_PROCESS_TRACE=NOT_INSTALLED_OFFSET_TYPO
R204B_MTOB_PRMLOAD_FILE_OPEN=PASS
R204B_MTOB_PRMLOAD_STATUS=2_PASS
R204B_MTOB_CHARSEL_FILE_OPEN=PASS
R204B_MTOB_CHARSEL_LOAD_COMPLETE=NOT_OBSERVED
R204B_MTOB_CHUNK_EVENTS=NONE_OBSERVED
R204C_PROCESS_OFFSET=0x116F404_VERIFIED
R204C_SOURCE_VERIFY=PASS
R204C_SOURCE_ZIP_POLICY=FLAT_ROOT
ID281_RANGE_NOT_REOPENED
```

---

# COMPLETE PRIOR MASTER HISTORY — R205 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R205 FULL
## CURRENT FRONTIER — R204A DIAGNOSTIC DID NOT INSTALL; R204B OPTIONAL-PROCESS TRACE READY

> **Authoritative current section.** R205 records the fresh `uzuy_log(30).txt` diagnostic run. The R204A ExeFS payload was loaded, but its all-or-nothing trace installer aborted because the historical `PROCESS` fingerprint at `main+0x106F404` no longer matched. The log explicitly reports `fingerprint FAIL PROCESS ...` followed by `[NSC:R204A] READY installed=0`. Therefore no R204A LOAD/FILE_OPEN/CHUNK evidence is valid from this run and no new gameplay/resource conclusion is drawn. R204B corrects only the diagnostic installer policy: LOAD_REQ, LOAD_CREATE, LOAD_STATUS, FILE_OPEN and CHUNK remain mandatory; PROCESS is now optional and cannot disable the five primary hooks.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change:
1. create/update the dated `NSC2Switch_MASTER_CHECKPOINT_<DATE>_<REV>_FULL.md`;
2. `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical to the current FULL checkpoint;
3. preserve the complete prior FULL checkpoint/history below the new authoritative section;
4. separate builder/tracer installation failures from runtime/gameplay conclusions;
5. do not reopen ID281 or frozen gameplay hypotheses without direct new evidence.

---

## 1. R204A FRESH RUNTIME RESULT — TRACE INSTALLATION FAIL

Fresh user log:

`uzuy_log(30).txt`

Observed boot/runtime identity:
- game update v1.70 applied;
- `main` Build ID queried as `48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39`;
- LayeredExeFS applied;
- R204A `subsdk9` executed through exlaunch.

Critical diagnostic lines:

```text
[NSC:P50A] fingerprint FAIL PROCESS off=0x106f404 word0=97fe40a7
[NSC:R204A] READY installed=0 readonly=1 fixture=mtob native_id_control=46 ...
```

Locked interpretation:
- R204A binary itself launched;
- `PROCESS` fingerprint was stale at the hard-coded offset;
- R204A `InstallTraceHooks()` used an all-or-nothing gate;
- because one optional diagnostic fingerprint failed, **none of the trace hooks were installed**;
- absence of R204A LOAD/FILE_OPEN/PROCESS/CHUNK lines is therefore expected and is not evidence that `mtob` paths were absent;
- R203A's Naruto-preview-empty hardware result remains the current gameplay observation;
- namespace/child/chunk root cause remains unresolved.

Markers:

`R204A_PAYLOAD_BOOT=PASS`

`R204A_PROCESS_FINGERPRINT=FAIL_STALE_OFFSET`

`R204A_TRACE_INSTALL=FAIL_ALL_OR_NOTHING_GATE`

`R204A_RUNTIME_RESOURCE_VERDICT=NO_DATA`

`R203A_PREVIEW_EMPTY=RETAINED`

`ID281_RANGE_NOT_REOPENED`

---

## 2. ROOT CAUSE IN R204A SOURCE

R204A's `InstallTraceHooks()` fingerprinted six boundaries before installing any hook:

- LOAD_REQ;
- LOAD_CREATE;
- LOAD_STATUS;
- CHUNK;
- PROCESS;
- FILE_OPEN.

The code set a shared `ok=false` when any single fingerprint failed, then returned before installing all six hooks. The fresh log emitted only the PROCESS fingerprint failure, strongly indicating the other five mandatory fingerprints still matched in this build. R204B removes PROCESS from the mandatory gate instead of changing gameplay behavior.

---

## 3. R204B — OPTIONAL-PROCESS READ-ONLY TRACE

Source kit:

`NSC2Switch_R204B_NATIVE_MTOB_TRACE_SOURCE.zip`

SHA256:

`faec7eebf7d572b07c782863ca727e693499e7df9c2ad608d61abda3bcd75e50`

Source verifier:

`R204B_SOURCE_VERIFY=PASS`

R204B behavior:
- no `main` override;
- no external ModdingAPI CPK bind;
- no numeric-ID patch;
- no path rewrite;
- no return-value override;
- no gameplay patch;
- track `mtob` even though the control slot is native CharacodeID 46;
- mandatory read-only hooks: LOAD_REQ, LOAD_CREATE, LOAD_STATUS, FILE_OPEN, CHUNK;
- optional read-only hook: PROCESS.

If the old PROCESS fingerprint remains mismatched, R204B prints:

```text
fingerprint FAIL R204B_PROCESS_OPTIONAL ...
```

but must continue and report:

```text
[NSC:R204B] READY installed=1 process_optional_installed=0 ...
```

The primary diagnostic is valid as long as `installed=1`.

---

## 4. R204B NEXT TEST

Keep the exact R203A RomFS `sound.cpk` carrier that produces the empty Naruto preview.

Add only the compiled R204B:

`atmosphere/contents/0100FA10190A0000/exefs/subsdk9`

Do not deploy:
- external `Tobi_Switch.cpk`;
- patched `main`;
- any other NSC2Switch ExeFS runtime.

Cold boot, hover the affected native Naruto slot once, then close the emulator and preserve the fresh full log.

Primary decision tree:

1. `READY installed=0` due a mandatory hook fingerprint:
   - fix only that boundary; no gameplay conclusion.
2. `FILE_OPEN ... result=0` or LOAD status error for first `mtob` path:
   - file/search-domain problem remains.
3. `LOAD_STATUS ... status=2` followed by `CHUNK ... result=0`:
   - XFBIN file loaded, but requested internal chunk/key does not resolve; next repair is internal namespace/key compatibility, not more blind file aliases.
4. `LOAD_STATUS ... status=2` and CHUNK result non-null for relevant preview paths while preview remains empty:
   - move downstream to actor/model construction.

---

## 5. STATUS

`R203A_NATIVE_NARUTO_PREVIEW=EMPTY`

`R204A_TRACE_INSTALL=FAIL`

`R204A_RUNTIME_RESOURCE_VERDICT=NO_DATA`

`R204B_SOURCE_VERIFY=PASS`

`R204B_HARDWARE=PENDING`

`SOUND_CPK_NATIVE_CARRIER=RETAINED`

`ID281_RANGE_NOT_REOPENED`

---

# COMPLETE PRIOR MASTER HISTORY — R204 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R204 FULL
## CURRENT FRONTIER — R203A PREVIEW ALIAS CONTROL DID NOT RESTORE NARUTO PREVIEW; R204A READ-ONLY NATIVE `mtob` LOAD/CHUNK TRACE READY

> **Authoritative current section.** R204 records the user's R203A hardware report: after deploying the native-ID46 `1nrt -> mtob` control with the additional direct preview aliases, Naruto's 3D hover preview still does not appear. This closes the four-alias batch as insufficient, but does not identify whether the remaining failure is file-open/load status, XFBIN processing, or internal chunk/key resolution. The next experiment is therefore a read-only loader/chunk trace on the exact R203A RomFS carrier. No ID281 work is reopened and no production dependency on `subsdk9` is introduced by this diagnostic.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change:
1. create/update the dated `NSC2Switch_MASTER_CHECKPOINT_<DATE>_<REV>_FULL.md`;
2. `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical to the current FULL checkpoint;
3. preserve the complete prior FULL checkpoint/history below the new authoritative section;
4. record exact build/hardware result, changed/unchanged state, hashes where relevant, and the next frontier;
5. do not silently convert a diagnostic `subsdk9` into a production runtime requirement.

---

## 1. R203A HARDWARE RESULT — NARUTO PREVIEW STILL EMPTY

User report:

`PREVIEW NARUTO GAK MUNCUL`

R203A purpose:
- stay on native Naruto CharacodeID 46;
- keep `characode 1nrt -> mtob`;
- retain the R200C native-Naruto `mtobprm_load` control;
- retain `mtobcharsel` cloned from native `1nrtcharsel`;
- add namespace aliases for the direct preview paths targeted by the previous runtime history:
  - `data/spc/mtobbod1.xfbin` <- native `1nrtbod1.xfbin` payload;
  - `data/spc/mtobbod1_col2.xfbin` <- native `1nrtbod1_col2.xfbin` payload;
  - `data/spc/mtobbod1_col3.xfbin` <- native `1nrtbod1_col3.xfbin` payload;
  - `data/spc/mtobbod1acc.bin.xfbin` <- native `1nrtbod1acc.bin.xfbin` payload.

Observed hardware outcome:

`R203A_NARUTO_HOVER_PREVIEW=EMPTY_REPORTED`

Because the user did not supply the R203A Termux build transcript in this turn, do not invent individual source CPK/hash/build markers beyond the already-produced R203A builder/package metadata. The hardware report is authoritative for preview behavior.

Locked interpretation:
- the four-file direct preview alias batch does not by itself restore the Naruto preview;
- R203A does **not** reopen numeric ID bounds because it remains on native ID46;
- R203A does **not** prove the parent `mtobprm_load` failed;
- R203A does **not** distinguish file-level load failure from internal XFBIN chunk/key mismatch;
- adding more guessed aliases without a fresh trace would no longer be controlled experimentation.

Markers:

`R203A_PREVIEW_ALIAS_CONTROL=NO_RECOVERY`

`R203A_HARDWARE=NARUTO_PREVIEW_EMPTY_REPORTED`

`ID281_RANGE_NOT_REOPENED`

---

## 2. R204A — READ-ONLY NATIVE `mtob` LOAD / CHUNK TRACE

R204A is a temporary diagnostic runtime derived from the current ModdingAPI Phase1 source tree.

It installs exactly the already-audited v1.70 trace boundaries:

- `main+0x1206B4C` — LOAD_REQ;
- `main+0x1206C9C` — LOAD_CREATE;
- `main+0x1207EFC` — LOAD_STATUS;
- `main+0x1170FB0` — FILE_OPEN;
- `main+0x106F404` — PROCESS/open-read result;
- `main+0x3EAE70` — `ccGetChunkBinary(full_path,key)` / CHUNK.

R204A uses the existing `mtob` path/key fallback, so it traces the current native-ID46 control even though ID46 is not a custom numeric ID.

R204A deliberately installs **none** of the following:
- external CPK bind;
- game `main` replacement;
- ID281/range expansion;
- characode/path rewrite;
- forced file status;
- forced return value;
- gameplay/UJ/D-pad patches;
- StageInfo mutation;
- resource injection.

Runtime core behavior for this diagnostic is reduced to:

`return nsc::InstallR204ANativeMtobTrace();`

Expected boot marker:

`[NSC:R204A] READY installed=1 readonly=1 ...`

Expected useful event classes:

`[NSC:R204A] LOAD_REQ ...`

`[NSC:R204A] LOAD_CREATE ...`

`[NSC:R204A] LOAD_STATUS ... status=...`

`[NSC:R204A] FILE_OPEN ... result=...`

`[NSC:R204A] PROCESS ... status=... readerr=...`

`[NSC:R204A] CHUNK path=... key=... result=...`

---

## 3. R204A SOURCE KIT

Artifact:

`NSC2Switch_R204A_NATIVE_MTOB_TRACE_SOURCE.zip`

SHA256:

`9f6478acb17db26c81a343ffb6ac2a548a6d058abfe90a6ce509f24a3b24bf3d`

Bytes:

`23197242`

Key source hashes:
- `nsc_runtime_core.cpp`: `4e8a88628a22bdbd2fd9372e9abf17f490607010f42fc664894e8325a2a6228f`;
- `nsc_cpk_bridge.cpp`: `9056f68fd850ce5df6c9973ef14f43f51275ed877f4f7e4e8c6a8289a7637781`;
- `analyze_r204a_log.py`: `cabc36fc002ff8b527ecc73ff11d3ee438e7371550d06960556ecd4191b27f46`.

Static source verification:

`R204A_SOURCE_VERIFY=PASS`

Verified properties:
- runtime core calls only the R204A trace installer;
- no gameplay installer remains in the R204A runtime core;
- trace wrapper is public and present;
- all six diagnostic event classes are present;
- `mtob` fixture fallback remains present;
- R204A wrapper does not install the external CPK binder.

The source kit includes a GitHub Actions workflow that packages only:

`runtime/atmosphere/contents/0100FA10190A0000/exefs/subsdk9`

and asserts no loose `main` is shipped.

`R204A_COMPILED_SUBSDK9=PENDING_GITHUB_ACTIONS`

---

## 4. R204A DEPLOYMENT / DECISION TREE

Build the R204A source kit using its included GitHub Actions workflow.

For the diagnostic run:
1. keep the exact R203A RomFS carrier that produced `NARUTO PREVIEW EMPTY`;
2. add only the compiled R204A `exefs/subsdk9`;
3. disable every other NSC2Switch ExeFS override and external ModdingAPI CPK;
4. cold boot;
5. enter character select;
6. hover the native Naruto slot once;
7. close the game/emulator and preserve the complete fresh log.

Analyze locally with:

`python3 analyze_r204a_log.py uzuy_log.txt`

Decision priority:

### A. First `FILE_OPEN ... result=0`
The exact path still fails at mounted-file open/search level. Fix only that path/carrier ownership next.

### B. `FILE_OPEN result=1`, then `PROCESS status=5` / nonzero read error
The file is found but native XFBIN/open-read processing rejects it. The next probe must compare raw/normalized transport semantics for that exact file.

### C. Child path reaches `LOAD_STATUS=2`, then `CHUNK ... result=0/null`
The XFBIN itself is loaded, but the requested internal key/chunk is not satisfied. This would directly support the internal `1nrt`-key vs `mtob`-key mismatch hypothesis and the next test should modify only the exact requested key/chunk boundary.

### D. All relevant files reach status2 and CHUNK results are non-null, preview still empty
Move downstream to character-select actor/model construction. Do not add more resource aliases.

### E. No R204A marker
Treat as diagnostic build/deployment failure, not a resource verdict.

---

## 5. STATUS

`R198A_NAMESPACE_VERDICT=INCONCLUSIVE_FIXTURE`

`SOUND_CPK_CHARACODE_PRECEDENCE=HARD_PASS_RETAINED`

`R200C_BUILD=PASS`

`R200C_NARUTO_HOVER_PREVIEW=EMPTY`

`R203A_PREVIEW_ALIAS_CONTROL=NO_RECOVERY`

`R203A_NARUTO_HOVER_PREVIEW=EMPTY_REPORTED`

`R204A_SOURCE_VERIFY=PASS`

`R204A_COMPILED_SUBSDK9=PENDING_GITHUB_ACTIONS`

`R204A_HARDWARE=PENDING`

`ID281_RANGE_NOT_REOPENED`

---

# COMPLETE PRIOR MASTER HISTORY — R203 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R203 FULL
## CURRENT FRONTIER — R200C BUILD PASS + NATIVE NARUTO PREVIEW EMPTY; DIRECT CHARACODE-DERIVED PREVIEW CHILD PATHS NOW PRIMARY SUSPECT; R203A READY

> **Authoritative current section.** R203 records the user's complete R200C Termux build and hardware result. The clean native-Naruto control built successfully with canonical v1.70 source hashes, native Naruto dynamically confirmed as CharacodeID 46, genuine `1nrtprm_load` sourced from base `data/launch/data1.cpk`, genuine `1nrtcharsel` sourced from base `data/launch/dataRegion.cpk`, all non-awakening/base resource placeholders pinned explicitly to known-good native `1nrt` children, and `mtobcharsel` cloned from the native Naruto charsel. The resulting R200C carrier contained exactly three files and booted, but the native Naruto hover/3D preview remained empty. This closes the Nanashi-fixture ambiguity and proves that `mtob` still lacks an additional preview dependency even on a clean native Naruto numeric/playerSetting/characterSelect fixture. Historical P30 tracing already identified a distinct direct characode-derived preview request wave (`mtobbod1`, `_col2`, `_col3`, `mtobcharsel`, `mtobbod1acc`) and native load errors for `mtobbod1acc` and `mtobbod1_col3`. R203 therefore moves the next data-only control to those direct namespace-derived child paths rather than reopening ID281 or parent `prm_load` registration.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change:
1. create/update the dated `NSC2Switch_MASTER_CHECKPOINT_<DATE>_<REV>_FULL.md`;
2. `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical to the current FULL checkpoint;
3. preserve the complete prior FULL checkpoint/history below the new authoritative section;
4. record exact builder output, source CPK/entry discovery, package hashes, hardware observation, and the next frontier;
5. do not convert a data-only diagnostic failure into an executable-range conclusion;
6. production architecture remains generic and must not hardcode Tobi/ID281-specific behavior.

---

## 1. R200C TERMUX BUILD — COMPLETE PASS

Canonical input gates:

```text
COMMON=a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27
SOUND=ec0e21c08f31d45a6e4efe902e2303609f4e03c39961f37f4560e884cefc4694
INPUT_GATES=PASS
```

Native resource ownership reproduced:

```text
PRMLOAD_SOURCE_CPK=.../base/romfs_nca/data/launch/data1.cpk
PRMLOAD_SOURCE_ENTRY=data/spcload/1nrtprm_load.bin.xfbin

CHARSEL_SOURCE_CPK=.../base/romfs_nca/data/launch/dataRegion.cpk
CHARSEL_SOURCE_ENTRY=data/ui/max/crsel/c/1nrtcharsel.xfbin
```

Native Naruto identity:

```text
CHARACODE_COUNT=280
NATIVE_1NRT_IDS=46
NATIVE_1NRT_ID=46
NATIVE_1NRT_BEFORE='1nrt'
NATIVE_1NRT_AFTER='mtob'
CHARACODE_OUTPUT_SHA256=70f622d499c1fe46482f16b3edc6722ce6837da95312f6f7ebf14ddea132b557
CHARACODE_NATIVE_NARUTO_MTOB_BUILD=PASS
```

Native `1nrtprm_load` facts:

```text
PRMLOAD_RAW_BYTES=728
PRMLOAD_PLAIN_BYTES=2416
PRMLOAD_RECORDS=26
PRMLOAD_PLACEHOLDER_REPLACEMENTS=18
PRMLOAD_DYNAMIC_PLACEHOLDERS_RETAINED=1
PRMLOAD_DYNAMIC_RETAIN row=14 '<codeAwakeModel>bod1'
PRMLOAD_BASE_CHILDREN_PINNED_TO_1NRT=PASS
PRMLOAD_OUTPUT_SHA256=5b9747ca8bea318940a5993b9e3c8f3ba640b02a6c7dc445d8cbb0e5eff70eaa
MTOB_PRMLOAD_NATIVE_1NRT_BASE_CHILDREN=PASS
```

Important explicit native child aliases created in the manifest include:

```text
1nrt_anmofs
1nrtbod1
1nrteff1
1nrtbod1c
1nrtbod1l
1nrtbod1s
1nrtskl1
1nrtskl2
1nrtskl3
1nrtspl1
1nrtprm.bin
1nrt_x
1nrtawa
1nrtspl1_bod1
1nrtdmg01_spl1_bod1
1nrt_comboPrm
```

The single `<codeAwakeModel>bod1` placeholder was intentionally retained rather than guessed and is not used as the primary hover-preview verdict.

Native charsel clone:

```text
CHARSEL_RAW_BYTES=167192
CHARSEL_PLAIN_BYTES=340297
MTOB_CHARSEL_SHA256=3ae948787c36eef30426824ecf7dd8772056ce51c85349bbd725262680d2218f
MTOB_CHARSEL_NATIVE_1NRT_CLONE=PASS
```

R200C carrier:

```text
Files: 3

data/spc/characode.bin.xfbin
data/spcload/mtobprm_load.bin.xfbin
data/ui/max/crsel/c/mtobcharsel.xfbin

R200C_CPK_SHA256=b561f71e17fba1bbc6feb6fa5d3ce635f17c1f1b65cee30658dabe258ab34e5b
R200C_CPK_BYTES=354448
R200C_ZIP_SHA256=37e7612b2c37e38f9d16492c10b7faccb9ac546376d640426fbb8db29983cb59
R200C_BUILD=PASS
```

Markers:

`R200C_INPUT_GATES=PASS`

`R200C_SOURCE_DISCOVERY=PASS`

`R200C_NATIVE_1NRT_CHARACODE_ID=46`

`R200C_PRMLOAD_BUILD=PASS`

`R200C_CHARSEL_CLONE=PASS`

`R200C_PACKING=PASS`

---

## 2. R200C HARDWARE RESULT — NATIVE NARUTO PREVIEW EMPTY

User hardware observation:

```text
NARUTO PREVIEW KOSONG
```

This result is now a valid clean fixture result because the actual native Naruto slot was used rather than Nanashi.

Locked interpretation:
- `patch/170/sound.cpk` characode precedence remains HARD PASS from R197A and is not reopened;
- native numeric CharacodeID remains 46, so ID281+ bounds are completely outside this test;
- native Naruto `playerSetting` / `characterSelect` relationships remain untouched;
- the new namespace `mtob` still fails to produce a hover preview even with the parent manifest transported and its base/model/motion FileName rows pinned back to known-good native Naruto resources;
- therefore a dependency exists outside those explicit `prm_load` FileName substitutions and outside the already-cloned `mtobcharsel` file path;
- do **not** classify this as proof that `mtobprm_load` itself cannot load, because historical P29/P30 runtime tracing already observed `data/spcload/mtobprm_load.bin.xfbin` reaching native `status=2 / IsLoaded` under the prior runtime baseline.

Markers:

`R200C_HARDWARE=PASS_BOOT_PREVIEW_EMPTY`

`R200C_NATIVE_NARUTO_PREVIEW=EMPTY`

`R200C_CLEAN_NAMESPACE_PREVIEW_CONTROL=FAIL_PREVIEW`

`ID281_RANGE_NOT_REOPENED`

`PARENT_PRMLOAD_FAILURE_NOT_PROVEN`

---

## 3. HISTORICAL P30 EVIDENCE NOW RELEVANT AGAIN

The older read-only P30 child trace established a direct preview request wave after `mtobprm_load` had already loaded successfully:

```text
data/spc/mtobbod1.xfbin
data/spc/mtobbod1_col2.xfbin
data/spc/mtobbod1_col3.xfbin
data/ui/max/crsel/c/mtobcharsel.xfbin
data/spc/mtobbod1acc.bin.xfbin
```

Confirmed native child errors included:

```text
data/spc/mtobbod1acc.bin.xfbin  status 0 -> 5
data/spc/mtobbod1_col3.xfbin    status 0 -> 5
```

P30 produced no custom CHUNK calls before those file-load failures, indicating the failure occurred at or before child XFBIN file-load completion rather than at a later chunk/key lookup.

The important architectural inference is that the preview subsystem derives at least some child filenames directly from the **active characode namespace**, independent of `prm_load` FileName rows. Therefore replacing `<codeModel>bod1` with explicit `1nrtbod1` inside R200C cannot satisfy all preview requests while the active characode remains `mtob`.

---

## 4. R203A — DIRECT CHARACODE-DERIVED PREVIEW ALIAS CONTROL

Builder:

`R203A_BUILD_MTOB_NATIVE_NARUTO_PREVIEW_ALIASES.sh`

SHA256:

`026feb6661a07c916c13602d2d4dbfadc1b40369d22f089e6ab81d7cf21eecfc`

Local validation:

`R203A_BUILDER_BASH_SYNTAX=PASS`

R203A preserves all R200C semantics and adds only four byte-exact native Naruto aliases under the direct `mtob`-derived preview paths:

```text
native 1nrtbod1.xfbin
  -> data/spc/mtobbod1.xfbin

native 1nrtbod1_col2.xfbin
  -> data/spc/mtobbod1_col2.xfbin

native 1nrtbod1_col3.xfbin
  -> data/spc/mtobbod1_col3.xfbin

native 1nrtbod1acc.bin.xfbin
  -> data/spc/mtobbod1acc.bin.xfbin
```

Source ownership is not hardcoded. The builder scans clean update170 CPKs first and then clean base CPKs, prints the exact source CPK and virtual entry for every alias, and stops if any native donor does not exist.

Expected R203A carrier file count:

```text
7
```

Expected virtual paths:

```text
data/spc/characode.bin.xfbin
data/spcload/mtobprm_load.bin.xfbin
data/ui/max/crsel/c/mtobcharsel.xfbin
data/spc/mtobbod1.xfbin
data/spc/mtobbod1_col2.xfbin
data/spc/mtobbod1_col3.xfbin
data/spc/mtobbod1acc.bin.xfbin
```

Still excluded:
- ID281+;
- `main` / `subsdk`;
- actual Tobi child payload;
- external ModdingAPI CPK;
- awakening/UJ judgment.

### R203A decision tree

**Naruto preview appears**
- direct characode-derived child filenames were the missing layer;
- native carrier transport can satisfy the new namespace when both manifest children and synthesized preview paths are provided;
- next step is to generalize alias/resource discovery for arbitrary mod characodes and progressively replace native aliases with actual mod assets.

**Naruto preview remains empty**
- do not reopen ID bounds;
- next boundary becomes either another synthesized preview dependency outside the first P30 wave or internal chunk/key identity inside the aliased XFBIN payloads;
- reintroduce read-only child `LOAD_STATUS`/`CHUNK` tracing against this native-carrier control before adding further resources blindly.

**Builder stops because a native `1nrt...` donor is absent**
- do not fabricate the file;
- record exact missing name and investigate the native path derivation/optional-resource semantics.

---

## 5. STATUS

`R198A_NAMESPACE_VERDICT=INCONCLUSIVE_FIXTURE`

`SOUND_CPK_CHARACODE_PRECEDENCE=HARD_PASS_RETAINED`

`R200C_BUILD=PASS`

`R200C_NATIVE_NARUTO_PREVIEW=EMPTY`

`DIRECT_CHARACODE_DERIVED_PREVIEW_PATHS=PRIMARY_SUSPECT`

`R203A_PREVIEW_ALIAS_CONTROL=READY`

`R203A_HARDWARE=PENDING`

`ID281_RANGE_NOT_REOPENED`

---

# COMPLETE PRIOR MASTER HISTORY — R202 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R202 FULL
## CURRENT FRONTIER — R200B SOURCE DISCOVERY PASS; NATIVE NARUTO ID46 CONFIRMED; R200C AWAKE-PLACEHOLDER-SAFE BUILDER READY

> **Authoritative current section.** R202 records the user's R200B Termux run. Clean v1.70 input hashes passed, the genuine native Naruto sources were located successfully, native `1nrt` was resolved dynamically as CharacodeID 46, and the `1nrt -> mtob` characode mutation rebuilt successfully. R200B then stopped before CPK packing because native `1nrtprm_load.bin.xfbin` contains one additional dynamic placeholder, `<codeAwakeModel>bod1`, not covered by the builder's base-code resolver. This is a builder placeholder-class issue only; no R200B carrier was produced and no hardware namespace verdict changed. R202 introduces R200C, which pins all base/model/motion Naruto child references to `1nrt` while intentionally preserving exactly the single native awakening-model placeholder instead of guessing its concrete awake resource.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change:
1. create/update the dated `NSC2Switch_MASTER_CHECKPOINT_<DATE>_<REV>_FULL.md`;
2. `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical to the current FULL checkpoint;
3. preserve the complete prior FULL checkpoint/history below the new authoritative section;
4. record exact build/hardware result, changed/unchanged state, hashes where relevant, and the next frontier;
5. do not convert builder/source-discovery failures into gameplay/runtime conclusions;
6. production architecture remains generic and must not hardcode Tobi/ID281-specific behavior.

---

## 1. R200B TERMUX RESULT — SOURCE DISCOVERY PASS, PREPACK PLACEHOLDER STOP

User output established:

```text
COMMON=a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27
SOUND=ec0e21c08f31d45a6e4efe902e2303609f4e03c39961f37f4560e884cefc4694
INPUT_GATES=PASS
CHARACODE_PATH=data/spc/characode.bin.xfbin

FOUND_PRMLOAD_CPK=/storage/emulated/0/Download/SWITCH/GAME/.nsc_uj_extract/base/romfs_nca/data/launch/data1.cpk
FOUND_PRMLOAD_ENTRY=data/spcload/1nrtprm_load.bin.xfbin

FOUND_CHARSEL_CPK=/storage/emulated/0/Download/SWITCH/GAME/.nsc_uj_extract/base/romfs_nca/data/launch/dataRegion.cpk
FOUND_CHARSEL_ENTRY=data/ui/max/crsel/c/1nrtcharsel.xfbin

NATIVE_1NRT_IDS=46
NATIVE_1NRT_ID=46
NATIVE_1NRT_BEFORE='1nrt'
NATIVE_1NRT_AFTER='mtob'
CHARACODE_OUTPUT_SHA256=70f622d499c1fe46482f16b3edc6722ce6837da95312f6f7ebf14ddea132b557
CHARACODE_NATIVE_NARUTO_MTOB_BUILD=PASS

STOP: unresolved dynamic placeholders: [(14, '<codeAwakeModel>bod1')]
```

Locked interpretation:
- canonical clean `patch/170/common.cpk`: PASS;
- canonical clean `patch/170/sound.cpk`: PASS;
- native Naruto `1nrtprm_load` ownership is now proven as base `data/launch/data1.cpk`;
- native Naruto charsel ownership is now proven as base `data/launch/dataRegion.cpk`;
- native Naruto CharacodeID is dynamically confirmed as **46** for this v1.70 dataset;
- `1nrt -> mtob` table mutation and semantic roundtrip validation: PASS;
- R200B stopped inside manifest placeholder expansion before carrier packing;
- no R200B `sound.cpk` probe was produced;
- no R200B hardware test exists;
- namespace verdict remains unchanged.

Markers:

`R200B_INPUT_GATES=PASS`

`R200B_NATIVE_1NRT_SOURCE_DISCOVERY=PASS`

`R200B_NATIVE_1NRT_CHARACODE_ID=46`

`R200B_CHARACODE_MUTATION=PASS`

`R200B_BUILD=STOP_PLACEHOLDER_CLASS`

`R200B_PACKING=NOT_REACHED`

`R200B_HARDWARE=NOT_RUN`

---

## 2. NEW NATIVE RESOURCE OWNERSHIP FACTS

For the clean extracted Connections dataset used by the project:

```text
Authoritative v1.70 characode table:
  update170/romfs_real/data/patch/170/common.cpk
  -> data/spc/characode.bin.xfbin

Native Naruto prm_load:
  base/romfs_nca/data/launch/data1.cpk
  -> data/spcload/1nrtprm_load.bin.xfbin

Native Naruto character-select preview payload:
  base/romfs_nca/data/launch/dataRegion.cpk
  -> data/ui/max/crsel/c/1nrtcharsel.xfbin
```

These ownership facts supersede the R200A assumption that all three resources belonged to `patch/170/common.cpk`.

---

## 3. R200B PLACEHOLDER FINDING

The native `1nrtprm_load` donor includes at least one placeholder class not handled by R200B's generic pinning logic:

```text
row 14: <codeAwakeModel>bod1
```

R200B already pins these placeholder families to explicit native Naruto `1nrt` child names:

```text
<code>
<codeModel>
<codeMotion>
<codeAwake>
```

`<codeAwakeModel>` is semantically different: its concrete resource code cannot be safely inferred from the characode string alone. Therefore the project must not fabricate a guessed awake-model resource merely to make the diagnostic build pass.

---

## 4. R200C — AWAKE-PLACEHOLDER-SAFE NATIVE NARUTO CONTROL

Builder:

`R200C_BUILD_MTOB_NATIVE_NARUTO_SOUND_CARRIER.sh`

SHA256:

`fa902909651360f2386630be043509999ef7ed3522180bf5df19369d3c4d36a2`

Local validation:

`R200C_BUILDER_BASH_SYNTAX=PASS`

R200C preserves the same R200/R200B experiment and changes only manifest validation:

1. clean source discovery remains data-driven;
2. native Naruto ID is still discovered dynamically; no ID46 hardcode is used for production logic;
3. only the discovered native `1nrt` characode entry is changed to `mtob`;
4. native `1nrtprm_load` remains the donor;
5. all base/model/motion `<code*>` child names are pinned explicitly to native `1nrt`;
6. exactly one dynamic placeholder is allowed to remain:

```text
<codeAwakeModel>bod1
```

7. any other unresolved `<code*>` placeholder still causes an immediate STOP;
8. the awake-model placeholder is intentionally preserved rather than guessed;
9. native `1nrtcharsel` is still cloned as `mtobcharsel`;
10. carrier target remains exactly three files under native `patch/170/sound.cpk`;
11. no ID281+, no `main`, no `subsdk`, no external ModdingAPI CPK, and no Tobi child resources are introduced.

The primary hardware question remains **hover/preview**, not awakening. Therefore retaining the native awakening-model placeholder does not contaminate the primary namespace transport discriminator. Awakening behavior is explicitly out of scope for this probe.

Expected R200C build markers include:

```text
PRMLOAD_DYNAMIC_PLACEHOLDERS_RETAINED=1
PRMLOAD_DYNAMIC_RETAIN row=14 '<codeAwakeModel>bod1'
PRMLOAD_BASE_CHILDREN_PINNED_TO_1NRT=PASS
MTOB_PRMLOAD_NATIVE_1NRT_BASE_CHILDREN=PASS
R200C_BUILD=PASS
```

---

## 5. NEXT FRONTIER

Run R200C against the same clean extraction.

### If `R200C_BUILD=PASS`
Deploy the generated R200C package **alone** and test the normal/native Naruto slot:
1. cold boot;
2. enter character select;
3. hover native Naruto;
4. record whether Naruto 3D preview appears;
5. if preview appears, selection/VS/battle may be checked secondarily;
6. do **not** judge awakening from this probe because the awake-model placeholder was intentionally left dynamic.

Interpretation:
- Naruto preview appears -> strong HARD PASS for new `mtob` namespace/resource transport through native `sound.cpk` on a coherent native fixture;
- native Naruto slot present but preview empty -> investigate namespace registration/dependent preview path; do not reopen numeric ID bounds;
- boot fail -> classify carrier/build compatibility before namespace verdict.

### If R200C still STOPs
Use the exact printed placeholder list. Do not invent replacements. The next step is to source-map only the newly exposed placeholder class/path.

---

## 6. STATUS

`R198A_NAMESPACE_VERDICT=INCONCLUSIVE_FIXTURE`

`SOUND_CPK_CHARACODE_PRECEDENCE=HARD_PASS_RETAINED`

`R200B_NATIVE_SOURCE_DISCOVERY=HARD_PASS`

`R200B_NATIVE_1NRT_CHARACODE_ID=46`

`R200B_CHARACODE_MUTATION=PASS`

`R200B_BUILD=STOP_PLACEHOLDER_CLASS`

`R200C_BUILDER=READY`

`R200C_HARDWARE=PENDING`

`ID281_RANGE_NOT_REOPENED`

---

# COMPLETE PRIOR MASTER HISTORY — R201 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R201 FULL
## CURRENT FRONTIER — R200A SOURCE-LOCATOR STOP; R200B DATA-DRIVEN NATIVE `1nrt` DONOR DISCOVERY READY

> **Authoritative current section.** R201 records the user's R200A Termux build result. Both canonical clean v1.70 hash gates passed, proving the expected `common.cpk` and `sound.cpk` inputs are intact. The builder then stopped before packing because its source-locator incorrectly assumed `data/spcload/1nrtprm_load.bin.xfbin` was owned by `patch/170/common.cpk`. This is a builder/source-ownership error only: no R200A carrier was produced and no new hardware namespace verdict exists. R201 replaces only that ownership assumption with a data-driven clean CPK scan while preserving the R200 clean native-Naruto control design.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change:
1. create/update the dated `NSC2Switch_MASTER_CHECKPOINT_<DATE>_<REV>_FULL.md`;
2. `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical to the current FULL checkpoint;
3. preserve the complete prior FULL checkpoint/history below the new authoritative section;
4. record exact build/hardware result, changed/unchanged state, hashes where relevant, and the next frontier;
5. do not convert a builder/source discovery failure into a gameplay/runtime conclusion.

---

## 1. R200A TERMUX BUILD RESULT — PREPACK STOP

User output:

```text
===== R200A BUNDLED PARSER =====
BUNDLED nsc_damage.py bytes=7059
BUNDLED nsc_ids.py bytes=18084
BUNDLED_PARSER_SELFTEST=PASS

===== R200A INPUT GATES =====
COMMON=a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27
SOUND=ec0e21c08f31d45a6e4efe902e2303609f4e03c39961f37f4560e884cefc4694
INPUT_GATES=PASS
STOP: 1nrtprm_load.bin.xfbin not found in clean common
```

Locked interpretation:
- clean `patch/170/common.cpk` identity: PASS;
- clean `patch/170/sound.cpk` identity: PASS;
- bundled parser self-test: PASS;
- build stopped before donor extraction / characode mutation / carrier packing;
- no R200A `sound.cpk` probe exists from this run;
- therefore there is **no new hardware result** and no namespace conclusion.

Markers:

`R200A_INPUT_GATES=PASS`

`R200A_BUILD=STOP_SOURCE_LOCATOR`

`R200A_PACKING=NOT_REACHED`

`R200A_HARDWARE=NOT_RUN`

`R200A_NAMESPACE_VERDICT=UNCHANGED`

---

## 2. ROOT CAUSE — CPK OWNERSHIP ASSUMPTION

R200A correctly sourced the authoritative v1.70 `characode.bin.xfbin` from `patch/170/common.cpk`, but incorrectly generalized that ownership to Naruto's per-character `1nrtprm_load.bin.xfbin`.

The failure does **not** justify substituting a different character manifest such as `9nnsprm_load`, because that would introduce a second semantic variable into the clean native-Naruto control. The donor must remain the genuine native `1nrtprm_load` if available in the clean extracted game data.

Therefore R200B changes only source discovery:
- `characode.bin.xfbin` remains sourced from the hash-gated clean `patch/170/common.cpk`;
- native `1nrtprm_load.bin.xfbin` is searched dynamically across clean update v1.70 CPKs first, then clean base CPKs;
- native `1nrtcharsel.xfbin` is resolved in the same single-pass scan;
- the first clean update hit wins over base, preserving patch precedence;
- exact source CPK and virtual entry paths are printed before extraction.

---

## 3. R200B — CORRECTED NATIVE-NARUTO BUILDER

Builder:

`R200B_BUILD_MTOB_NATIVE_NARUTO_SOUND_CARRIER.sh`

SHA256:

`0b2ea51041b78d18896139a9a7435dd7215f56e10748f6879cb8817df36d464b`

Local validation:

`R200B_BUILDER_BASH_SYNTAX=PASS`

Unchanged experiment semantics:
1. verify canonical clean `common.cpk` and `sound.cpk` hashes;
2. parse native `characode.bin.xfbin`;
3. locate the unique native `1nrt` CharacodeID dynamically;
4. mutate only that native entry `1nrt -> mtob`;
5. use the genuine native `1nrtprm_load.bin.xfbin` as donor;
6. expand its `<code*>` child placeholders explicitly back to native `1nrt` children;
7. clone native `1nrtcharsel.xfbin` as `data/ui/max/crsel/c/mtobcharsel.xfbin`;
8. pack exactly the three diagnostic files into native `patch/170/sound.cpk`;
9. no ID281+, no `main`, no `subsdk`, no Tobi child asset, no external ModdingAPI CPK.

New source-discovery output expected before build stages:

```text
FOUND_PRMLOAD_CPK=...
FOUND_PRMLOAD_ENTRY=.../1nrtprm_load.bin.xfbin
FOUND_CHARSEL_CPK=...
FOUND_CHARSEL_ENTRY=.../1nrtcharsel.xfbin
PRMLOAD_SOURCE_CPK=...
PRMLOAD_SOURCE_ENTRY=...
CHARSEL_SOURCE_CPK=...
CHARSEL_SOURCE_ENTRY=...
```

If no genuine native `1nrtprm_load.bin.xfbin` exists anywhere in the clean update/base CPK set, the builder must stop and that absence becomes the next forensic question. It must not fabricate a donor.

---

## 4. NEXT FRONTIER

Run R200B in Termux against the same clean extraction.

### Build PASS
Expected terminal marker:

`R200B_BUILD=PASS`

Then deploy the generated R200B probe alone and test the normal/native Naruto slot.

### Source discovery STOP
If R200B reports:

`STOP: could not locate native 1nrtprm_load.bin.xfbin in clean update/base CPKs`

then do **not** proceed to hardware. Capture the printed scan outcome and move to the native `1nrt` load-manifest ownership/alias question.

No ID281 work is reopened until this clean native-Naruto namespace control is resolved.

---

## 5. STATUS

`R198A_NAMESPACE_VERDICT=INCONCLUSIVE_FIXTURE`

`SOUND_CPK_CHARACODE_PRECEDENCE=HARD_PASS_RETAINED`

`R200A_INPUT_GATES=PASS`

`R200A_BUILD=STOP_SOURCE_LOCATOR`

`R200B_SOURCE_DISCOVERY=READY`

`R200B_HARDWARE=PENDING`

`ID281_RANGE_NOT_REOPENED`

---

# COMPLETE PRIOR MASTER HISTORY — R200 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R200 FULL
## CURRENT FRONTIER — R198A NANASHI PREVIEW EMPTY IS INCONCLUSIVE; R200A NATIVE-NARUTO `1nrt -> mtob` CONTROL READY

> **Authoritative current section.** R200 records the user's R198A hardware observation that the Nanashi hover/3D preview does not appear. This does **not** establish that the new `mtob` namespace failed, because R199 had already established that the Nanashi fixture itself is not a clean hover-preview discriminator: in R197A the Nanashi hover preview was also empty even though post-selection resource identity resolved to Naruto through the known-good native `1nrt` namespace. R200 therefore retires the Nanashi-based R198A preview result as **inconclusive for namespace registration** and advances to the clean control already specified by R199: mutate the genuine native Naruto `1nrt` slot to `mtob` while preserving its vanilla numeric/playerSetting/characterSelect relationships.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change:
1. create/update the dated `NSC2Switch_MASTER_CHECKPOINT_<DATE>_<REV>_FULL.md`;
2. `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical to the current FULL checkpoint;
3. preserve the complete prior FULL checkpoint/history below the new authoritative section;
4. record exact hardware result, changed/unchanged state, hashes where relevant, and the next test frontier;
5. do not silently reopen already-frozen hypotheses.

---

## 1. R198A HARDWARE RESULT — USER REPORT

Probe under test:
- native numeric ID280 / Nanashi fixture;
- `characode ID280: 9nns -> mtob`;
- `data/spcload/mtobprm_load.bin.xfbin` cloned from native `9nnsprm_load`;
- `<code*>` child names expanded explicitly to known-good native `9nns` resources;
- carrier: `data/patch/170/sound.cpk`;
- no ID281+;
- no `main`/`subsdk`;
- no Tobi child resource;
- no external ModdingAPI CPK.

User hardware observation:

`NANASHI PREVIEW GAK MUNCUL`

Locked marker:

`R198A_NANASHI_HOVER_PREVIEW=EMPTY_REPORTED`

---

## 2. CORRECT INTERPRETATION — DO NOT CALL THIS A NAMESPACE FAIL

R198A's empty Nanashi hover preview is **not a clean namespace verdict**.

Reason:
- R197A already proved that the same Nanashi fixture can have an empty hover preview while the post-selection model still resolves to Naruto using the known-good native `1nrt` namespace;
- therefore the Nanashi slot has an independent hover-preview/fixture mismatch and cannot isolate `mtob` registration;
- `patch/170/sound.cpk` characode consumption remains HARD PASS from R197A;
- the result does not reopen ID281 bounds and does not invalidate the native sound carrier.

Locked markers:

`R198A_NAMESPACE_VERDICT=INCONCLUSIVE_FIXTURE`

`SOUND_CPK_CHARACODE_PRECEDENCE=HARD_PASS_RETAINED`

`ID281_RANGE_NOT_REOPENED`

`NANASHI_HOVER_PIPELINE_NOT_VALID_AS_NAMESPACE_ORACLE`

---

## 3. R200A — CLEAN NATIVE NARUTO NEW-NAMESPACE CONTROL

New builder:

`R200A_BUILD_MTOB_NATIVE_NARUTO_SOUND_CARRIER.sh`

SHA256:

`d624164fb5044f8bad7725a2ebff2cf6a6209200e2e21c83dc12728890b504c7`

Builder design:

1. Verify clean v1.70 source hashes:
   - `common.cpk` SHA256 `a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27`;
   - `sound.cpk` SHA256 `ec0e21c08f31d45a6e4efe902e2303609f4e03c39961f37f4560e884cefc4694`.

2. Parse clean `data/spc/characode.bin.xfbin`.

3. Locate the genuine native Naruto `1nrt` CharacodeID **dynamically**. No numeric Naruto ID is hardcoded.

4. Change only that native slot:

```text
1nrt -> mtob
```

All other characode rows remain byte-semantically unchanged.

5. Extract clean native:

`data/spcload/1nrtprm_load.bin.xfbin`

and build:

`data/spcload/mtobprm_load.bin.xfbin`

Every `<code*>` FileName placeholder is expanded explicitly back to native `1nrt` resource names. The new namespace key is `mtob`, but its child resources remain known-good native Naruto assets.

6. Locate clean native:

`data/ui/max/crsel/c/1nrtcharsel.xfbin`

by scanning the clean update/base extracted CPKs instead of assuming its source CPK.

7. Normalize/decode that native Naruto charsel and transport it unchanged internally as:

`data/ui/max/crsel/c/mtobcharsel.xfbin`

This ensures a constructed `mtobcharsel` lookup can resolve to a known-good Naruto character-select preview payload.

8. Pack a tiny native carrier containing exactly three virtual files:

```text
data/patch/170/sound.cpk
├── data/spc/characode.bin.xfbin
├── data/spcload/mtobprm_load.bin.xfbin
└── data/ui/max/crsel/c/mtobcharsel.xfbin
```

9. Ship:
- no custom ID281+;
- no `main`;
- no `subsdk`;
- no Tobi child assets;
- no external ModdingAPI CPK.

The builder passed local shell syntax validation:

`R200A_BUILDER_BASH_SYNTAX=PASS`

---

## 4. R200A HARDWARE TEST

Deploy **R200A alone** with every other NSC2Switch override disabled.

Test:
1. cold boot;
2. enter character select;
3. hover the normal/native Naruto slot affected by `1nrt -> mtob`;
4. observe 3D preview;
5. if preview appears, select Naruto and continue through VS/battle as a secondary confirmation.

### HARD PASS — Naruto preview appears

Interpretation:
- genuine native Naruto slot retained valid numeric/playerSetting/characterSelect relationships;
- `characode=mtob` is active;
- new `mtobprm_load` transport/registration works from native `patch/170/sound.cpk`;
- `mtobcharsel` lookup is satisfied;
- explicit native `1nrt` child resources resolve through the new namespace.

Then next:
- keep the same native carrier architecture;
- progressively substitute actual Tobi `mtob` child resources for the native Naruto children;
- only after namespace/resource transport remains proven, restore the minimal **generic** ID281+ admission/consumer expansion.

### NATIVE NARUTO SLOT PRESENT, PREVIEW EMPTY/MISSING

Interpretation:
- carrier/characode precedence remains proven;
- because this test uses a coherent native Naruto fixture, the remaining blocker is now genuinely in new namespace registration and/or an additional dependent resource/registration path;
- do **not** blame ID bounds because the numeric ID remains vanilla.

Next frontier in that branch:
- inspect native `prm_load`/charsel lookup and one-shot registration semantics;
- compare native `1nrt` lookup requests against `mtob`;
- do not add Tobi children yet.

### BOOT FAIL

Interpret first as:
- source extraction mismatch;
- CPK rebuild compatibility;
- malformed normalized donor payload;
- unexpected clean-source ownership.

Do not classify namespace failure until packaging is cleared.

---

## 5. FROZEN RESULTS RETAINED

- `R196A_SOUND_PLAYER_ICON_SENTINEL=HARD_PASS`;
- `CONNECTIONS_PATCH170_SOUND_CROSS_FAMILY_CARRIER=HARD_PASS`;
- `R197A_SOUND_CHARACODE_SENTINEL=HARD_PASS_CONSUMED`;
- `R197A_HOVER_PREVIEW=EMPTY`;
- `R197A_POST_SELECTION_MODEL=NARUTO`;
- R164 StageInfo hardware PASS/frozen;
- R172 UJ hardware PASS/frozen;
- P128 admission/session frozen;
- P33A `Sorted=0` lookup lesson remains required;
- R189A 1.2 GiB architecture remains retired;
- combined donor `fb7ca9...d5488` remains four-character source-of-truth;
- final architecture remains generic and must not hardcode Tobi/ID281.

---

## 6. STATUS

`R198A_NANASHI_HOVER_PREVIEW=EMPTY_REPORTED`

`R198A_NAMESPACE_VERDICT=INCONCLUSIVE_FIXTURE`

`R200A_NATIVE_1NRT_MTOB_CONTROL=READY_TO_BUILD`

`R200A_BUILDER_BASH_SYNTAX=PASS`

`SOUND_CPK_CHARACODE_PRECEDENCE=HARD_PASS_RETAINED`

`ID281_RANGE_NOT_REOPENED`

---

# COMPLETE PRIOR MASTER HISTORY — R199 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R199 FULL
## CURRENT FRONTIER — R197A CHARACODE CARRIER CONSUMED; HOVER PREVIEW EMPTY / POST-SELECTION MODEL RESOLVES NARUTO

> **Authoritative current section.** R199 resolves the apparent R197A report conflict. The supplied screenshot and user description show that the `patch/170/sound.cpk` characode sentinel is consumed: native Nanashi ultimately resolves to a Naruto model after selection. However, the user separately confirms that the initial hover/3D preview is empty. Therefore R197A is a hard PASS for `characode.bin.xfbin` carrier precedence/consumption, but not a full PASS for the hover-preview pipeline.

---

## 0. CHECKPOINT DISCIPLINE

Preserve the complete prior FULL checkpoint verbatim below this section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must remain byte-identical.

---

## 1. R197A HARDWARE RESULT — RESOLVED

Probe:
- carrier: `data/patch/170/sound.cpk`;
- internal payload: `data/spc/characode.bin.xfbin`;
- only semantic change: native CharacodeID 280 `9nns -> 1nrt`;
- no custom ID281+;
- no ExeFS/main/subsdk;
- no external ModdingAPI CPK.

Observed:
- game booted successfully;
- the initial hover/3D preview is empty;
- after selection, the Nanashi slot resolves to a Naruto 3D model;
- screenshot shows the selected 1P entry still labeled Nanashi while the rendered model is Naruto;
- user notes a small eye/face visual bug.

The eye/face artifact is treated as a fixture mismatch between Nanashi-owned surrounding parameters/costume state and the forced Naruto characode identity. It is not evidence that the carrier failed.

---

## 2. LOCKED INTERPRETATION

The sound carrier definitely overrides/feeds `characode.bin.xfbin` strongly enough to alter character resource identity.

Locked markers:

`R197A_BOOT=PASS`

`SOUND_CPK_CHARACODE_PRECEDENCE=HARD_PASS`

`R197A_POST_SELECTION_MODEL=NARUTO`

`R197A_HOVER_PREVIEW=EMPTY`

Therefore:
- `patch/170/sound.cpk` cross-family carrier behavior now has HARD PASS evidence for both `player_icon` and `characode` consumers;
- hover-preview is a separate downstream consumer/state and is not satisfied by the characode-only mutation on a native Nanashi fixture;
- do not downgrade the proven carrier mechanism because of the empty hover preview;
- do not treat the eye/face mismatch as a new namespace failure.

---

## 3. NEXT CLEAN NAMESPACE CONTROL

The next probe should avoid ID281+ and avoid the incoherent Nanashi->Naruto fixture.

Preferred control:
1. locate a native Naruto `1nrt` CharacodeID dynamically from clean `characode.bin.xfbin`;
2. keep that native Naruto slot and all its existing playerSetting/characterSelect relationships intact;
3. change only that native characode string `1nrt -> mtob`;
4. provide `data/spcload/mtobprm_load.bin.xfbin` through the proven `patch/170/sound.cpk` carrier;
5. clone/rename the native `1nrt` prm_load namespace to `mtob` while mapping child resource names back to proven native `1nrt` assets, so no custom Tobi child resource is required;
6. provide `data/ui/max/crsel/c/mtobcharsel.xfbin` cloned from the native `1nrtcharsel` if the charsel path is constructed from characode;
7. keep numeric ID inside vanilla range and ship no ExeFS patch.

Decision:
- Naruto slot/model survives through namespace `mtob` -> genuinely new `mtob` namespace/prm_load registration works from the native sound carrier;
- slot identity changes but preview/resource load fails -> carrier table precedence works, but new namespace registration or a dependent path is still missing;
- boot fail -> classify build/CPK compatibility first.

Only after a clean native-ID `mtob` namespace PASS should actual Tobi child resources replace the native `1nrt` children.

---

## 4. FROZEN RESULTS RETAINED

- `R196A_SOUND_PLAYER_ICON_SENTINEL=HARD_PASS`;
- `CONNECTIONS_PATCH170_SOUND_CROSS_FAMILY_CARRIER=HARD_PASS`;
- R184 A/B frozen/pending;
- R164 StageInfo hardware PASS/frozen;
- R172 UJ hardware PASS/frozen;
- P128 admission/session frozen;
- P33A Sorted=0 lookup lesson;
- R189A 1.2 GiB architecture retired;
- combined donor `fb7ca9...d5488` remains four-character source-of-truth;
- production architecture remains generic.

---

## 5. STATUS

`R196A_SOUND_PLAYER_ICON_SENTINEL=HARD_PASS`

`R197A_SOUND_CHARACODE_SENTINEL=HARD_PASS_CONSUMED`

`R197A_HOVER_PREVIEW=EMPTY`

`R197A_POST_SELECTION_MODEL=NARUTO`

`NEXT_NATIVE_ID_MT0B_NAMESPACE_PROBE=READY_TO_BUILD`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R198 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R198 FULL
## CURRENT FRONTIER — R197A HARDWARE REPORT CONFLICT; SCREENSHOT SHOWS NARUTO RESOLUTION, TEXT SAYS PREVIEW EMPTY

> **Authoritative current section.** R198 records a conflicting hardware report for R197A. The supplied screenshot visibly shows the native Nanashi slot resolving to a Naruto 3D model after the `characode` sentinel `9nns -> 1nrt`, but the immediately following text report says `BOOT PASS — PREVIEW KOSONG`. Because those two observations conflict, R198 does not finalize the R197A verdict until the user identifies which observation is authoritative or whether they came from different packages/runs.

---

## 0. CHECKPOINT DISCIPLINE

Preserve the complete prior FULL checkpoint verbatim below this section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must remain byte-identical.

---

## 1. R197A HARDWARE OBSERVATION — CONFLICTING REPORTS

R197A probe design:
- outer carrier: `data/patch/170/sound.cpk`;
- internal payload: `data/spc/characode.bin.xfbin`;
- only semantic change: native CharacodeID 280 `9nns -> 1nrt`;
- no custom ID281+;
- no `main`/`subsdk`;
- no external ModdingAPI CPK.

Observed visual evidence from the supplied screenshot:
- game booted;
- character-select screen loaded;
- the 1P slot is still labeled Nanashi;
- the displayed 3D character model is Naruto;
- user explicitly reported: `nanashi jadi naruto, tapi mata nya ngebug aja`.

Immediately afterward, user also reported:

`BOOT PASS — PREVIEW KOSONG`

These statements are mutually inconsistent if they refer to the same R197A run/state.

---

## 2. TEMPORARY CLASSIFICATION

Confirmed regardless of ambiguity:

`R197A_BOOT=PASS`

Not yet finalized:

`R197A_CHARACODE_PRECEDENCE=AMBIGUOUS_PENDING_USER_CLARIFICATION`

If the screenshot/report `Nanashi -> Naruto` is authoritative, classify:
- `SOUND_CPK_CHARACODE_PRECEDENCE=HARD_PASS`;
- the minor eye/face glitch is a fixture mismatch artifact and not a carrier failure;
- proceed to the new-namespace control using native ID280 + `mtobprm_load`.

If `PREVIEW KOSONG` is authoritative for the same R197A package/run, classify:
- `sound.cpk` can override the characode table but the resulting resource resolution failed before model preview;
- do not claim full characode identity PASS;
- inspect whether `1nrt` resource registration/path ownership differs from the historical P27A environment.

If the two observations came from different packages/runs, record them separately and keep the package identity with each result.

---

## 3. FROZEN RESULTS RETAINED

The following remain unchanged:
- `R196A_SOUND_CARRIER_BOOT=PASS`;
- `R196A_SOUND_PLAYER_ICON_SENTINEL=HARD_PASS`;
- `CONNECTIONS_PATCH170_SOUND_CROSS_FAMILY_CARRIER=HARD_PASS`;
- R184 A/B frozen/pending;
- R164 StageInfo hardware PASS/frozen;
- R172 UJ hardware PASS/frozen;
- P128 admission/session frozen;
- P33A Sorted=0 lookup lesson;
- R189A 1.2 GiB architecture retired.

---

## 4. STATUS

`R197A_BOOT=PASS`

`R197A_SCREENSHOT_NANASHI_TO_NARUTO=OBSERVED`

`R197A_TEXT_REPORT_PREVIEW_EMPTY=OBSERVED`

`R197A_FINAL_VERDICT=PENDING_CLARIFICATION`

`CONNECTIONS_PATCH170_SOUND_CROSS_FAMILY_CARRIER=HARD_PASS`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R197 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R197 FULL
## CURRENT FRONTIER — PATCH/170 SOUND.CPK CROSS-FAMILY CARRIER HARDWARE PASS; CHARACODE PRECEDENCE PROBE READY

> **Authoritative current section.** R197 records the first decisive hardware proof that Connections v1.70 `data/patch/170/sound.cpk` can act as an RTB-style cross-family native CPK carrier. A one-file replacement `sound.cpk` containing only `data/spc/player_icon.xfbin` booted successfully and overrode the active player-icon table: native Nanashi displayed the Sasuke icon exactly as the structured sentinel specified. This proves the carrier mechanism itself. R197 now isolates whether the same carrier also wins for `data/spc/characode.bin.xfbin` before testing a genuinely new `mtob` namespace/prm_load.

---

## 0. CHECKPOINT DISCIPLINE

Preserve the complete prior FULL checkpoint verbatim below this section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must remain byte-identical.

---

## 1. R196A HARDWARE RESULT — HARD PASS

User hardware result:

`BOOT PASS — NANASHI ICON SASUKE`

R196A deployed a tiny diagnostic replacement:

```text
data/patch/170/sound.cpk
  └─ data/spc/player_icon.xfbin
```

The payload was the already semantically validated R192A V3 player-icon sentinel:
- CharacodeID 280 rows: 3
- BaseIcon changed to `ssk3`
- all other record semantics preserved

Observed hardware:
- game booted;
- character select was reachable;
- native Nanashi small icon resolved as Sasuke.

Therefore:

`CONNECTIONS_PATCH170_SOUND_CROSS_FAMILY_CARRIER=HARD_PASS`

`SOUND_CPK_PLAYER_ICON_PRECEDENCE=HARD_PASS`

This is direct evidence that the outer native mount name `sound.cpk` does not constrain internal virtual path family and that the resolver accepts `data/spc/*` from this carrier with winning precedence.

This reproduces the key Storm 4 RTB carrier concept on Connections for at least one authoritative `data/spc` consumer.

---

## 2. ARCHITECTURAL CONSEQUENCE

The previous external ModdingAPI CPK bridge is no longer the only known way to expose arbitrary mod data paths.

Proven native transport option:

```text
data/patch/170/sound.cpk
  -> arbitrary internal virtual paths
  -> game resolver
```

This is separate from numeric character expansion.

Still unresolved:
1. whether `characode.bin.xfbin` also resolves from this carrier before character resource registration;
2. whether a genuinely new `<characode>prm_load.bin.xfbin` namespace is enumerated/registered when supplied by this native carrier;
3. ID281+ remains subject to the known Connections executable enumeration/consumer bounds.

---

## 3. R197A — CHARACODE PRECEDENCE CONTROL

Before testing `mtob`, R197A keeps the carrier and numeric ID native.

New builder:

`R197A_BUILD_CHARACODE_SOUND_CARRIER_SENTINEL.sh`

SHA256:

`e4d1b03cb635929bb2a6e15f119341481e9fe5b3ea68a36f9d15f80402345904`

Inputs:
- clean v1.70 common SHA256
  `a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27`
- clean v1.70 sound SHA256
  `ec0e21c08f31d45a6e4efe902e2303609f4e03c39961f37f4560e884cefc4694`

R197A extracts clean:

`data/spc/characode.bin.xfbin`

The builder bundles the alpha13e parser modules required to:
- normalize/decrypt/decompress the raw XFBIN;
- parse the 280-entry native characode list;
- assert ID280 is `9nns`;
- change only ID280 to `1nrt`;
- rebuild and semantic-verify the table.

Diagnostic CPK:

```text
data/patch/170/sound.cpk
  └─ data/spc/characode.bin.xfbin
```

No player_icon sentinel is included.

---

## 4. WHY `9nns -> 1nrt` IS THE NEXT CLEAN CONTROL

Historical P27A already proved that switching a characode string to native `1nrt` drives preview/resource identity while keeping the numeric slot path valid.

R197A applies that same semantic discriminator to native ID280:
- ID280 remains inside all vanilla bounds;
- roster/playerSetting/characterSelect stay untouched;
- no custom `prm_load` is needed;
- no custom UI symbol is needed;
- no Tobi asset is needed.

Expected hardware result:

### PASS
Nanashi roster slot/icon may remain visually Nanashi, but hover/3D preview becomes Naruto.

Interpretation:
- `patch/170/sound.cpk` wins for `characode.bin.xfbin`;
- characode identity is available from the carrier early enough to drive preview;
- proceed directly to R197B/R198 new-namespace control:
  - ID280 `9nns -> mtob`;
  - `mtobprm_load.bin.xfbin` supplied from the same carrier;
  - child resources controlled independently.

### NO EFFECT
Nanashi preview remains Nanashi.

Interpretation:
- sound-carrier precedence is consumer/path dependent;
- player_icon PASS cannot automatically be generalized to characode;
- inspect load order/ownership before a custom namespace test.

### BOOT FAIL
Treat as characode sentinel/rebuild compatibility first, not namespace verdict.

---

## 5. NEXT NEW-NAMESPACE PROBE DESIGN — HELD UNTIL R197A RESULT

The intended next discriminator is now cleaner than shipping Tobi's full asset set.

Preferred design:
- keep native ID280;
- set characode ID280 to `mtob`;
- supply `data/spcload/mtobprm_load.bin.xfbin` from the proven `sound.cpk` carrier;
- use a manifest whose child resource names resolve to proven native `9nns` assets.

If preview still resolves successfully, the result will prove that a genuinely new `mtob` namespace/prm_load can be registered through the native carrier without involving ID281 or missing custom child resources.

Only after that proof should actual Tobi child assets be substituted.

---

## 6. FROZEN STATE

No verdict changes for:
- R184 A/B: frozen/pending;
- R164 StageInfo: hardware PASS/frozen;
- R172 UJ: hardware PASS/frozen;
- P128 admission/session: frozen;
- voice: frozen;
- D-pad historical state;
- P33A `Sorted=0` lookup lesson remains mandatory for larger generated custom carriers;
- R189A 1.2 GiB architecture remains retired;
- combined donor `fb7ca9...d5488` remains the four-character source-of-truth;
- production architecture remains generic.

---

## 7. STATUS

`R192A_V3_MOVIE1_BOOT=PASS`

`R192A_V3_MOVIE1_SENTINEL=NO_EFFECT`

`R196A_SOUND_CARRIER_BOOT=PASS`

`R196A_SOUND_PLAYER_ICON_SENTINEL=HARD_PASS`

`CONNECTIONS_PATCH170_SOUND_CROSS_FAMILY_CARRIER=HARD_PASS`

`R197A_CHARACODE_SOUND_CARRIER_BUILDER=READY`

`R197A_HARDWARE=PENDING`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R196 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R196 FULL
## CURRENT FRONTIER — R192A V3 HARDWARE NO-EFFECT; PATCH/170 SOUND CARRIER PROBE READY

> **Authoritative current section.** R196 records the first hardware result of the correctly built tiny `launch/movie1.cpk` carrier sentinel: the game booted normally, but native Nanashi's icon remained unchanged. Therefore the `launch/movie1.cpk` carrier did not win for the v1.70 `player_icon` consumer. The RTB-style native-carrier hypothesis remains open; the next controlled probe moves the same proven sentinel to `data/patch/170/sound.cpk`, the closest Connections analog to RTB `patch/3/sound.cpk`.

---

## 0. CHECKPOINT DISCIPLINE

Preserve the complete prior FULL checkpoint verbatim below this section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must remain byte-identical.

---

## 1. R192A V3 HARDWARE RESULT — BOOT PASS / SENTINEL NO EFFECT

User hardware result:

`BOOT PASS — NANASHI ICON TETAP NORMAL`

Interpretation:
- rebuilt base `data/launch/movie1.cpk` is boot-compatible;
- its original movie payload preservation was sufficient for boot;
- the cross-family `data/spc/player_icon.xfbin` sentinel did not override the active v1.70 player-icon source;
- this result does **not** reject native cross-family carrier behavior generally;
- it specifically rejects `launch/movie1.cpk` as a winning carrier for this later v1.70 `player_icon` consumer under this test.

Markers:

`R192A_V3_BOOT=PASS`

`R192A_V3_PLAYER_ICON_SENTINEL=NO_EFFECT`

`CONNECTIONS_MOVIE1_CROSS_FAMILY_CARRIER_FOR_PLAYER_ICON=NO`

---

## 2. WHY THIS RESULT IS USEFUL

R192A V3 isolated transport/precedence without:
- custom character IDs;
- `main`;
- `subsdk0`;
- `subsdk9`;
- external ModdingAPI CPK;
- Tobi/Toneri/Itachi resources;
- custom loose GFX.

Therefore the result is not confounded by the character-expander or custom namespace problem.

The next probe should preserve the exact same sentinel semantics and change only the outer native CPK mount slot.

---

## 3. R196A — TINY PATCH/170 SOUND.CPK CARRIER PROBE

New builder:

`R196A_BUILD_TINY_SOUND_CARRIER_SENTINEL.sh`

SHA256:

`dbacec095e5dbc725e424cf27ed25acbc455a68eed1ebe65a4eda58aded701e2`

Purpose:
test whether Connections `data/patch/170/sound.cpk` can act as a cross-family virtual-path carrier like Storm 4 RTB `data/patch/3/sound.cpk`.

Inputs:
- clean v1.70 `patch/170/sound.cpk`
  - expected SHA256 `ec0e21c08f31d45a6e4efe902e2303609f4e03c39961f37f4560e884cefc4694`
- exact validated R192A V3 sentinel `player_icon.xfbin`
  - expected SHA256 `3d5dcbd4b7be6d074925537966d3d1829e52962c6b5da677f3636fe2716a5d09`

R196A deliberately builds a one-file diagnostic CPK:

```text
data/patch/170/sound.cpk
  └─ data/spc/player_icon.xfbin
```

This is intentionally tiny and diagnostic. It does **not** preserve the 295 clean v1.70 sound entries.

Reason for the tiny-first design:
- avoid immediately rebuilding/shipping the full ~474 MiB update sound archive;
- test whether the native sound mount accepts and exposes the cross-family virtual path at all;
- if the game still boots, the icon result is highly informative;
- if boot fails, the result is ambiguous because required sound update payloads were omitted, and the next control must be a full-preserve clean sound rebuild plus the same sentinel.

---

## 4. R196A HARDWARE DECISION MATRIX

Deploy R196A alone with all other NSC2Switch overrides disabled.

Test:
1. cold boot;
2. if boot succeeds, enter character select;
3. inspect native Nanashi small icon.

### A. BOOT PASS + NANASHI = SASUKE
`patch/170/sound.cpk` cross-family carrier PASS.

This would strongly reproduce the RTB carrier mechanism in Connections.

Next:
- keep `patch/170/sound.cpk` as candidate carrier;
- build a minimal custom-resource namespace probe;
- keep numeric-ID expansion separate.

### B. BOOT PASS + NANASHI NORMAL
The native sound mount did not win for this consumer or did not expose this path.

Next:
- inspect mount order / path filtering;
- consider another native patch carrier or a thin external CPK mount runtime.

### C. BOOT FAIL
Do **not** conclude carrier failure.

This tiny probe intentionally removes the native 295-file sound payload.

Next:
- R196B full-preserve sound control:
  - extract all 295 clean sound entries;
  - add only the same validated `player_icon` sentinel;
  - repack with no other mod data;
  - repeat the hardware sentinel test.

---

## 5. FROZEN STATE

No verdict changes for:
- R184 A/B: frozen/pending;
- R164 StageInfo: hardware PASS/frozen;
- R172 UJ: hardware PASS/frozen;
- P128 admission/session: frozen;
- voice: frozen;
- D-pad historical state;
- P33A `Sorted=0` lookup lesson;
- R189A 1.2 GiB architecture remains retired;
- combined donor `fb7ca9...d5488` remains source-of-truth;
- production policy remains generic.

---

## 6. STATUS

`R192A_V3_BUILD=PASS_STATIC`

`R192A_V3_BOOT=PASS`

`R192A_V3_SENTINEL=NO_EFFECT`

`R196A_TINY_SOUND_CARRIER_BUILDER=READY`

`R196A_HARDWARE=PENDING`

`R189A_HARDWARE_TEST=RETIRED`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R195 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R195 FULL
## CURRENT FRONTIER — R192A V3 TINY MOVIE1 CARRIER BUILD PASS / HARDWARE SENTINEL PENDING

> **Authoritative current section.** R195 records successful construction of the first correctly built tiny Connections `data/launch/movie1.cpk` cross-family carrier sentinel. This is a static/build PASS only. No hardware carrier/precedence PASS is claimed until the user tests the package on Switch.

---

## 0. CHECKPOINT DISCIPLINE

Preserve the complete prior FULL checkpoint verbatim below this section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must remain byte-identical.

---

## 1. R192A V3 USER BUILD — PASS

User executed:

`R192A_V3_BUILD_MOVIE1_CARRIER_SENTINEL.sh`

Bundled parser self-test:

```text
BUNDLED nsc_damage.py bytes=7059
BUNDLED nsc_ids.py bytes=18084
BUNDLED nsc_core.py bytes=16661
BUNDLED nsc_secondary.py bytes=12265
BUNDLED_PARSER_SELFTEST=PASS
```

Clean input gates:

```text
MOVIE  c1cd43af4b4d32c8b380a1d51cc61b0fcbb3d6237873161d07faf2a9d6e586f1
COMMON a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27
INPUT_GATES=PASS
```

---

## 2. STRUCTURED PLAYER_ICON SENTINEL — PASS

Clean v1.70 `data/spc/player_icon.xfbin` extraction:

- raw bytes: **7,796**
- normalized bytes: **31,512**
- decode path: **cc2_decrypt -> crilayla_decompress**
- records: **465**
- native CharacodeID 280 rows: **3**

Observed target rows before mutation:

```text
row 462 BaseIcon='nns1' strings=('nns1', 'nns_awk9', 'nns1', 'nns_1')
row 463 BaseIcon='nns2' strings=('nns2', '', 'nns3', 'nns_1')
row 464 BaseIcon='nns1' strings=('nns1', '', 'nns1', 'nns_1')
```

After structured rebuild:

```text
row 462 BaseIcon='ssk3'
row 463 BaseIcon='ssk3'
row 464 BaseIcon='ssk3'
```

Semantic guard result:

`PLAYER_ICON_SENTINEL_BUILD=PASS`

Only the three native ID280 rows were changed semantically, and only their BaseIcon field was changed.

Rebuilt normalized `player_icon.xfbin`:

```text
bytes  26,815
SHA256 3d5dcbd4b7be6d074925537966d3d1829e52962c6b5da677f3636fe2716a5d09
```

---

## 3. TINY MOVIE1 CROSS-FAMILY CARRIER — BUILD PASS

Generated CPK:

```text
Mode      1
Files     2
Alignment 2048
Version   CPKMC2.30.07, DLL3.00.07
```

Exact internal files:

```text
data/movie_sw/na_0000_000.usm
data/spc/player_icon.xfbin
```

Carrier output:

```text
bytes  36,212,872
SHA256 a447e067fd6863b39e3f6c1f522dc1f608a94f330647d92d3ddb705290049af4
```

Marker:

`R192A_V3_CARRIER_FILES=2`

---

## 4. FINAL R192A V3 PACKAGE — BUILD PASS

Output:

`$HOME/NSC2Switch_R192A_V3_MOVIE1_CARRIER_SENTINEL.zip`

Observed size: approximately **35 MiB**.

SHA256:

`54f3bf8bd521c80390757971170e14fb3819fbb65a64dbc8957e6430835214fc`

Marker:

`R192A_V3_BUILD=PASS`

This replaces the failed V1/V2 builders as the authoritative carrier-sentinel build.

---

## 5. REQUIRED HARDWARE TEST — CARRIER ONLY

Deploy R192A V3 **alone**.

The only active NSC2Switch override for the probe must be:

```text
atmosphere/contents/0100FA10190A0000/
  romfs/data/launch/movie1.cpk
```

Temporarily disable:
- `exefs/main`
- `subsdk0`
- `subsdk9`
- `romfs/data/moddingapi/Tobi_Switch.cpk`
- custom `patch/170/common.cpk`
- custom `patch/170/sound.cpk`
- custom `patch/170/movie.cpk`
- custom loose `charicon_s.gfx`
- any other NSC2Switch roster/resource override

Test only:
1. cold boot;
2. enter character select;
3. inspect native Nanashi small icon.

Decision:

### PASS
Nanashi uses Sasuke / follows `ssk3`.

This proves:
- Connections `data/launch/movie1.cpk` can expose cross-family `data/spc/*`;
- this early native carrier wins precedence for `player_icon`;
- the RTB-style native carrier concept transfers to Connections for this consumer.

Next after PASS:
- preserve the same carrier mechanism;
- add a minimal real custom-resource transport probe (`prm_load` + one custom namespace subset);
- keep numeric ID expansion separate.

### NO EFFECT
Nanashi remains normal.

This means:
- the `launch/movie1.cpk` carrier either loses to later v1.70 ownership or is not searched for `player_icon`.

Next:
- run the exact same structured sentinel through native `patch/170/sound.cpk`, the closer RTB `patch/3/sound.cpk` analog.

### BOOT FAIL
Treat as CPK replacement/repack compatibility first. Do not interpret as a new-slot or namespace verdict.

---

## 6. FROZEN STATE

No verdict changes for:
- R184 A/B: frozen/pending;
- R164 StageInfo: hardware PASS/frozen;
- R172 UJ: hardware PASS/frozen;
- P128 admission/session: frozen;
- voice: frozen;
- D-pad historical state;
- P33A `Sorted=0` lesson;
- R189A 1.2 GiB architecture remains retired;
- production policy remains generic, not Tobi/ID281-specific.

---

## 7. STATUS

`R192A_V1_SENTINEL_BUILD=FAIL_BAD_RAW_STRING_ASSUMPTION`

`R192A_V2_BUILD=FAIL_LOCAL_PARSER_DISCOVERY`

`R192A_V3_BUNDLED_PARSER_SELFTEST=PASS`

`R192A_V3_PLAYER_ICON_SENTINEL=PASS_STATIC`

`R192A_V3_CARRIER_BUILD=PASS_STATIC`

`R192A_V3_HARDWARE=PENDING`

`CONNECTIONS_MOVIE1_CROSS_FAMILY_CARRIER=PENDING`

`R189A_HARDWARE_TEST=RETIRED`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R194 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R194 FULL
## CURRENT FRONTIER — R192A V2 TOOLCHAIN-PATH GATE FAIL; SELF-CONTAINED V3 BUILDER READY

> **Authoritative current section.** R194 records that R192A V2 did not reach input hashing, CPK packing, or hardware because the script could not locate the alpha13e parser modules under the user's current `~/nsc_switch_tool` layout. This is a local toolchain-discovery failure only. The carrier hypothesis remains untested. R194 replaces the dependency lookup with a self-contained V3 builder that embeds the exact alpha13e parser modules required for `player_icon` normalization/parsing.

---

## 0. CHECKPOINT DISCIPLINE

Preserve the complete prior FULL checkpoint verbatim below this section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must remain byte-identical.

---

## 1. R192A V2 USER EXECUTION — TOOLCHAIN DISCOVERY FAIL

Observed user output:

```text
STOP: NSC2Switch Python parser not found.
Expected nsc_damage.py + nsc_core.py + nsc_secondary.py under ~/nsc_switch_tool
```

Interpretation:
- no clean CPK input was modified;
- no sentinel payload was generated;
- no replacement `movie1.cpk` was packed;
- no hardware test occurred;
- no carrier/precedence verdict changed.

Marker:

`R192A_V2_BUILD=FAIL_LOCAL_PARSER_DISCOVERY`

---

## 2. ALPHA13E PARSER RECOVERY

The archived `NSC2Switch_v0.3-alpha13e.zip` was inspected directly.

Required parser modules are present:
- `nsc_damage.py`
- `nsc_ids.py`
- `nsc_core.py`
- `nsc_secondary.py`

Important dependency correction:
- `nsc_core.py` imports `nsc_damage` and `nsc_ids`;
- `nsc_secondary.py` imports `nsc_damage`, `nsc_ids`, and `nsc_core`.

Therefore V2's three-file existence gate was incomplete as a portability contract even though it matched one historical working tree.

---

## 3. R192A V3 — SELF-CONTAINED BUILDER

New builder:

`R192A_V3_BUILD_MOVIE1_CARRIER_SENTINEL.sh`

SHA256:

`47173b5fb9252cd517976eab01950f7abddccbfa87a114e0e84f65e2047ae8c8`

V3 embeds the exact alpha13e source modules:
- `nsc_damage.py`
- `nsc_ids.py`
- `nsc_core.py`
- `nsc_secondary.py`

At runtime V3 writes them into its temporary work directory and uses that directory as `PYTHONPATH`.

It no longer requires:
- `~/nsc_switch_tool`;
- an installed alpha13e tree;
- parser files to exist anywhere outside the script.

V3 still requires only ordinary external tools already used by the project:
- Python;
- `cpk-tool`;
- `sha256sum`;
- `zip`.

---

## 4. V3 LOCAL SELF-TEST — PASS

V3 was syntax-checked and its bundled parser was executed independently before release.

Observed:

```text
BUNDLED nsc_damage.py bytes=7059
BUNDLED nsc_ids.py bytes=18084
BUNDLED nsc_core.py bytes=16661
BUNDLED nsc_secondary.py bytes=12265
BUNDLED_PARSER_SELFTEST=PASS
R192A_V3_SELFTEST_ONLY=PASS
```

Self-test validates:
- alpha13e modules import successfully from the embedded temporary tree;
- `PLAYER_ICON_SPEC.record_size == 0x28`;
- `PLAYER_ICON_SPEC.pointer_offsets == (0x08, 0x10, 0x18, 0x20)`.

A pre-release self-test bug using obsolete attribute names `stride` / `string_offsets` was caught locally and corrected before V3 release.

---

## 5. HARDWARE QUESTION — UNCHANGED

V3 still tests only resource transport / carrier precedence.

If build succeeds, deploy only:

```text
atmosphere/contents/0100FA10190A0000/
  romfs/data/launch/movie1.cpk
```

with all other NSC2Switch overrides disabled.

Test:
1. cold boot;
2. enter character select;
3. inspect native Nanashi small icon.

Decision:
- Nanashi follows `ssk3` / Sasuke -> `launch/movie1.cpk` cross-family carrier PASS;
- no effect -> launch carrier loses precedence or is not searched for `player_icon`; next controlled carrier is `patch/170/sound.cpk`;
- boot fail -> classify as movie1 CPK rebuild/compatibility issue first.

No new-slot, ID-expander, Tobi, UJ, StageInfo, or R184 verdict changes in R194.

---

## 6. STATUS

`R192A_V1_SENTINEL_BUILD=FAIL_BAD_RAW_STRING_ASSUMPTION`

`R192A_V2_BUILD=FAIL_LOCAL_PARSER_DISCOVERY`

`R192A_V3_BUNDLED_PARSER_SELFTEST=PASS`

`R192A_V3_BUILDER=READY`

`CONNECTIONS_MOVIE1_CROSS_FAMILY_CARRIER=PENDING`

`R189A_HARDWARE_TEST=RETIRED`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R193 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R193 FULL
## CURRENT FRONTIER — R192A V1 SENTINEL BUILDER GATE FAIL; STRUCTURED PLAYER_ICON V2 READY

> **Authoritative current section.** R193 records that R192A did not reach CPK packing or hardware. The clean input gates passed, but the v1 builder stopped because it incorrectly assumed the raw CPK-extracted `player_icon.xfbin` would contain plaintext `9nns` bytes. The carrier hypothesis itself remains untested. R193 replaces only the sentinel-construction method with a structured XFBIN/table parser derived from the existing NSC2Switch alpha13e+ compiler path.

---

## 0. CHECKPOINT DISCIPLINE

Preserve the complete prior FULL checkpoint verbatim below this section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must remain byte-identical.

---

## 1. R192A V1 USER EXECUTION — INPUT GATES PASS, SENTINEL BUILD FAIL

User ran `R192A_BUILD_MOVIE1_CARRIER_SENTINEL.sh` in Termux.

Observed:

```text
MOVIE=c1cd43af4b4d32c8b380a1d51cc61b0fcbb3d6237873161d07faf2a9d6e586f1
COMMON=a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27
INPUT_GATES=PASS
PLAYER_ICON_PATH=data/spc/player_icon.xfbin
Extracted: data/movie_sw/na_0000_000.usm (34.50 MB)
Extracted: data/spc/player_icon.xfbin (7.61 KB)
STOP: no exact 9nns bytes found in player_icon
```

Interpretation:
- clean base `movie1.cpk` identity is still correct;
- clean v1.70 `common.cpk` identity is still correct;
- `player_icon.xfbin` path discovery/extraction succeeded;
- no replacement `movie1.cpk` was packed;
- no hardware test occurred;
- this result says nothing about movie1 carrier precedence.

Marker:

`R192A_V1_SENTINEL_BUILD=FAIL_BAD_RAW_STRING_ASSUMPTION`

---

## 2. ROOT CAUSE

Historical P22 described an in-place semantic BaseIcon substitution inside an already-normalized/compiled `player_icon` payload. R192A v1 incorrectly generalized that to the raw v1.70 CPK-extracted payload and searched directly for ASCII `9nns`.

The existing NSC2Switch alpha13e+ compiler proves the correct format handling:
- raw XFBIN payload may require CC2 decrypt and/or CRILAYLA decompression;
- `PLAYER_ICON_SPEC` record stride is `0x28`;
- player icon string-pointer slots are `(0x08, 0x10, 0x18, 0x20)`;
- `BaseIcon` is semantic `strings[0]`, pointer slot `0x08`;
- player icon records are keyed by numeric CharacodeID.

Therefore the sentinel must patch the parsed records for native CharacodeID 280, not search the raw extracted bytes for the characode string `9nns`.

---

## 3. R192A V2 BUILDER

New builder:

`R192A_V2_BUILD_MOVIE1_CARRIER_SENTINEL.sh`

SHA256:

`8d6403f3f31ae74e2376d857b7ed76656a817ec3cd1824770abfb91eaa09ceb1`

V2 algorithm:
1. hash-gate the same clean base movie1 and clean v1.70 common inputs;
2. extract only original `data/movie_sw/na_0000_000.usm` from base movie1;
3. extract clean `data/spc/player_icon.xfbin` from common;
4. run `normalize_xfbin_payload` using the installed NSC2Switch parser;
5. parse `PLAYER_ICON_SPEC` fixed-string records;
6. select every record where `CharacodeID == 280`;
7. replace only `strings[0]` / BaseIcon with `ssk3`;
8. preserve fixed bytes and all other string fields semantically;
9. rebuild the XFBIN and parse it again;
10. assert only target ID280 rows changed semantically;
11. pack `movie1.cpk` with exactly two files: original movie + sentinel player_icon.

The rebuilt `player_icon` is allowed to be normalized plaintext NUCC and need not match the compressed/encrypted raw source byte size. The semantic table is the invariant.

---

## 4. R192A V2 HARDWARE QUESTION — UNCHANGED

Deploy V2 alone with no other NSC2Switch overrides.

Test:
- cold boot;
- enter character select;
- inspect native Nanashi small icon.

Decision:
- Nanashi follows `ssk3` / Sasuke icon -> `launch/movie1.cpk` cross-family carrier/precedence PASS for `data/spc/player_icon.xfbin`;
- no effect -> this launch carrier loses precedence or is not searched for this consumer; next controlled test is the same structured sentinel through native `patch/170/sound.cpk`;
- boot fail -> classify as movie1 CPK rebuild/compatibility problem first.

No new-slot, ID-expander, Tobi, UJ, StageInfo, or R184 verdict changes in R193.

---

## 5. STATUS

`R192A_V1_INPUT_GATES=PASS`

`R192A_V1_SENTINEL_BUILD=FAIL_BAD_RAW_STRING_ASSUMPTION`

`R192A_V1_HARDWARE=NOT_RUN`

`R192A_V2_BUILDER=READY`

`CONNECTIONS_MOVIE1_CROSS_FAMILY_CARRIER=PENDING`

`R189A_HARDWARE_TEST=RETIRED`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R192 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R192 FULL
## CURRENT FRONTIER — TINY `launch/movie1.cpk` CROSS-FAMILY CARRIER SENTINEL BUILDER READY

> **Authoritative current section.** R192 converts the R191 RTB native-carrier hypothesis into a minimal controlled Connections probe. It does **not** restore the retired R189A 1.2 GiB architecture and does **not** claim hardware PASS. The next probe changes only transport/precedence: a rebuilt base `data/launch/movie1.cpk` preserves its single original movie payload and adds one modified v1.70 `data/spc/player_icon.xfbin` sentinel.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

Every project update must preserve the complete previous FULL checkpoint verbatim below the new authoritative section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical.

---

## 1. R192 TRIGGER / CORRECTION HELD

R189A remains retired for hardware deployment.

Do not merge complete clean `common.cpk` + `sound.cpk` payloads into the modpack again merely to make custom resources native-owned.

R191 separation remains authoritative:
1. resource transport / namespace visibility;
2. numeric character expansion.

R192 tests only item 1.

---

## 2. WHY THE SENTINEL USES `player_icon.xfbin`

Historical P22A already produced a hardware-PASS source sentinel:
- Nanashi ID280 BaseIcon was redirected to `ssk3`;
- Tobi ID281 BaseIcon was redirected to `gar4`;
- hardware showed Nanashi as Sasuke and Tobi as Gaara.

Therefore `player_icon.xfbin` is a proven visually observable consumer and avoids inventing a new diagnostic path.

R192A reuses only the Nanashi-side mapping:

```text
9nns -> ssk3
```

This is a same-length four-byte in-place substitution. The XFBIN size and pointer layout are preserved.

---

## 3. R192A CARRIER DESIGN

Source inputs are the already frozen clean hashes:

```text
base data/launch/movie1.cpk
SHA256 c1cd43af4b4d32c8b380a1d51cc61b0fcbb3d6237873161d07faf2a9d6e586f1

v1.70 data/patch/170/common.cpk
SHA256 a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27
```

Clean base `movie1.cpk` owns exactly one known payload:

```text
data/movie_sw/na_0000_000.usm
```

R192A rebuild tree contains exactly two files:

```text
data/movie_sw/na_0000_000.usm      <- preserved clean base payload
data/spc/player_icon.xfbin          <- authoritative v1.70 table with 9nns->ssk3 sentinel
```

No Tobi/Toneri/Itachi resource is needed for this test.
No new character ID is needed.
No character-expander result is being tested.

---

## 4. R192A BUILDER

Generated script:

```text
R192A_BUILD_MOVIE1_CARRIER_SENTINEL.sh
SHA256 ec4db98262ba25a23ee4cd810e47a5f2ca7ad89f4fcf8637ec4adab187ef90f3
```

The builder:
- hash-gates the clean base movie1 and v1.70 common sources;
- extracts only the original base movie payload;
- locates/extracts `player_icon.xfbin` from clean v1.70 common;
- performs same-size exact-byte `9nns -> ssk3` substitution;
- repacks a mode-1 `movie1.cpk` from only those two files;
- asserts both internal paths survived;
- asserts exactly two CPK files;
- packages only `romfs/data/launch/movie1.cpk` for Atmosphere deployment.

Expected probe size is on the order of the original ~36 MiB movie carrier, not 1+ GiB.

---

## 5. R192A DEPLOYMENT CONTRACT

Deploy R192A **alone** for the carrier test.

Temporarily disable/remove all other NSC2Switch overrides for this run:
- no `exefs/main`;
- no `subsdk0`;
- no `subsdk9`;
- no `romfs/data/moddingapi/Tobi_Switch.cpk`;
- no custom `patch/170/common.cpk`;
- no custom `patch/170/sound.cpk`;
- no custom `patch/170/movie.cpk`;
- no custom loose `charicon_s.gfx`.

The only active override should be:

```text
atmosphere/contents/0100FA10190A0000/
  romfs/data/launch/movie1.cpk
```

---

## 6. HARDWARE DECISION MATRIX

Test only:
1. cold boot;
2. enter character select;
3. inspect native Nanashi small icon.

Interpretation:

### PASS — Nanashi icon resolves as Sasuke / follows `ssk3`
This proves that Connections' native `data/launch/movie1.cpk` mount can expose a cross-family internal `data/spc/*` path and that this carrier wins for the `player_icon` consumer.

Next: build R192B/R193 real-resource transport probe using the same carrier mechanism before reintroducing the minimal generic ID expander.

### NO EFFECT — Nanashi remains normal
This does **not** prove native carriers are impossible. It means this specific base `launch/movie1.cpk` either loses precedence to the later v1.70 source or is not searched for this consumer.

Next: run the same proven `player_icon` sentinel through native `patch/170/sound.cpk`, which is the closer analog to RTB `patch/3/sound.cpk`.

### BOOT FAIL
Treat as a base-movie CPK rebuild/compatibility problem first. Do not interpret it as a namespace/new-slot verdict.

---

## 7. FROZEN STATE

No verdict changes for:
- R184 A/B: frozen/pending;
- R164 StageInfo: hardware PASS/frozen;
- R172 UJ: hardware PASS/frozen;
- P128 admission/session: frozen;
- voice: frozen;
- D-pad historical state;
- P33A `Sorted=0` lesson for generated custom CPK lookup;
- production policy remains generic, not ID281-specific.

---

## 8. STATUS

`R189A_HARDWARE_TEST=RETIRED`

`R192A_MOVIE1_CARRIER_SENTINEL_BUILDER=READY`

`R192A_HARDWARE=PENDING`

`RTB_NATIVE_CPK_CARRIER_MODEL=CONFIRMED_FOR_STORM4`

`CONNECTIONS_MOVIE1_CROSS_FAMILY_CARRIER=PENDING`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R191 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R191 FULL
## CURRENT FRONTIER — R189A FULL-NATIVE-CPK MERGE RETIRED; RTB NATIVE-CARRIER MECHANISM REFOCUSED

> **Authoritative current section.** R191 records the user's correction that the R189A/R190 1.2 GiB full `common.cpk` + `sound.cpk` transplant is the wrong architecture target. R189A remains a valid static build artifact only, but its hardware deployment is retired. The active branch returns to direct Storm 4 RTB forensic evidence to identify the smallest mechanism that makes added roster/resource data visible on Switch.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

Every project update must preserve the complete previous FULL checkpoint verbatim below the new authoritative section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical.

---

## 1. R189A / R190 CORRECTION

R189A generated:
- `common.cpk`: 925 files, SHA256 `2259e0fbfa4a358df841b9688526510ae51ae8ea895bc82edae132c54aed6236`;
- `sound.cpk`: 318 files, SHA256 `c79f89c01f24a97086b861320325aa575cb574c001c62dfd1f5cc513ed438c3f`;
- package: approximately 1.2 GiB, SHA256 `0ede90798da1bd3506b60b28987dedd28f92b0a71bd79470d0b33e9e9e2174d4`.

Static gates were valid, but the architecture is now **RETIRED FOR HARDWARE TESTING** because it duplicates/rebuilds large native CPK payloads rather than reproducing the mechanism used by the RTB Switch modpack.

Markers:

`R189A_BUILD=PASS_STATIC_ONLY`

`R189A_HARDWARE_TEST=RETIRED`

`R189A_ARCHITECTURE=DEAD_END_FULL_NATIVE_MERGE`

Do not deploy the 1.2 GiB R189A package as the next experiment.

---

## 2. RTB OUTER PACKAGE — NO SWITCH EXECUTABLE HOOK FOUND

Direct forensic inspection of the Storm 4 RTB Switch pack established:
- package contains `Mod/romfs/...` only;
- no `exefs/main`;
- no `subsdk*`;
- no IPS executable patch;
- no custom Switch runtime loader.

Therefore no packaged Switch-side executable hook has been found that explains its visible added roster.

The PC Perfect-Storm/Storm 4 ModdingAPI does contain a separate character-limit expander and runtime executable patching capability, but those binaries are not present in this Switch AIO package. Do not infer that the PC 65,535-character expander is running on Switch.

---

## 3. ACTUAL RTB SWITCH MECHANISM — NATIVE CPK CARRIER / VIRTUAL PATH OVERRIDE

Observed RTB layout:

```text
Mod/romfs/data/launch/movie1.cpk             1,350,480 bytes
Mod/romfs/data/patch/3/sound.cpk         3,395,027,792 bytes
Mod/romfs/data/ui/flash/OTHER/...        loose UI GFX overrides
```

### `movie1.cpk`
- 10 files;
- alignment 512;
- small early/high-priority delta;
- includes `duel/unlockCharaTotal.bin.xfbin`;
- includes `spcload/1tmrprm_load.bin.xfbin`;
- includes character-specific `spc/*` payload.

### `patch/3/sound.cpk`
- 5,380 files;
- alignment 512;
- is not audio-only despite its filename;
- internal virtual paths include `data/spc`, `data/spcload`, `data/duel`, `data/ui/max/select`, `data/ui/max/crsel/c`, icon paths, sound, stage, effect and other resource families;
- contains the core roster/select datasets including `unlockCharaTotal`, `duelPlayerParam`, `playerSettingParam`, `skillCustomizeParam`, `spTypeSupportParam`, and `characterSelectParam`.

Key interpretation:

**The RTB package uses an already-native-mounted CPK slot as a general virtual data carrier. The outer filename `sound.cpk` does not restrict the internal path families that the game's CPK/VFS resolver can expose.**

This native mount behavior is the closest thing to the requested "hook" found in the Switch package.

---

## 4. INDEPENDENT COMMUNITY CORROBORATION

GBAtemp Storm 4 Switch modding reports describe the same porting model:
- build PC-style data into a Switch CPK;
- rename relevant `WIN64` content to `SWITCH`;
- use `data/launch/movie1.cpk` for ordinary data mods;
- for Ultimate AIO, map the PC patch folder to Switch patch `3` and replace `sound.cpk`;
- community users reported the Ultimate AIO characters loading on Switch.

This corroborates the forensic package structure and does not indicate a hidden ExeFS patch.

---

## 5. WHAT MAKES THE RTB "NEW SLOT" DATA-DRIVEN

The evidence supports a multi-table/resource registration path, not a single roster file:
- `unlockCharaTotal.bin.xfbin` — playability/unlock set;
- `duelPlayerParam.xfbin` — character/resource definitions;
- `playerSettingParam.bin.xfbin` — preset/character/message mappings;
- `characterSelectParam.xfbin` — character-select roster/layout;
- `skillCustomizeParam.xfbin` / `spTypeSupportParam.xfbin` — gameplay parameter relations;
- `spcload/*prm_load.bin.xfbin` — per-character resource manifests;
- matching `spc`, UI, icon, effect, stage and sound resources;
- loose GFX registrations for selection UI.

The RTB AIO `duelPlayerParam` contains 217 unique `*prm_bas.bin` source-name codes. This is evidence of a large data-driven resource census, not proof of 217 independently playable slots.

Still unresolved:
- whether the RTB Switch AIO exceeds Storm 4's native numeric roster ceiling at all;
- whether it mainly consumes already-available/unused native ranges;
- the exact clean-vs-AIO table delta for each added slot.

A clean Storm 4 Switch `patch/3/sound.cpk` or equivalent registry baseline is required for a definitive delta.

---

## 6. WHY THIS DOES NOT DIRECTLY REMOVE CONNECTIONS' EXPANDER

Connections v1.70 has a proven native hard boundary around custom IDs:
- vanilla active `prm_load` enumeration terminates before custom ID281;
- historical character-expander work modifies the core enumeration/resolver/data/battle bounds;
- P27A showed numeric ID281/PSP527+ can work when resource identity is redirected to a valid namespace under the expander lineage.

Therefore the RTB data-only carrier result does **not** prove that Connections ID281+ can run with vanilla executable bounds.

The correct separation is now:
1. **resource transport / namespace visibility** — investigate RTB-style native carrier CPK versus external CPK binder;
2. **numeric character expansion** — retain a minimal generic Connections expander until disproven unnecessary.

---

## 7. CONNECTIONS NATIVE CARRIER CANDIDATES

Connections update inventory proves native mounts exist for:
- `data/patch/170/common.cpk` — authoritative latest roster/global data;
- `data/patch/170/sound.cpk` — native sound patch, approximately 473.72 MiB;
- base `data/launch/movie1.cpk` — 36,182,528 bytes, one movie payload in the clean base.

Do not repeat R189A by merging the complete native `common.cpk` and `sound.cpk` contents with the modpack.

New research question:

**Can an existing Connections native CPK mount slot expose arbitrary internal virtual paths with the same cross-family behavior seen in RTB, so the current ~393 MiB combined mod ecosystem can stay compact?**

Candidate tests must first prove carrier-path precedence with a tiny sentinel before packaging the full character ecosystem.

---

## 8. NEXT FORENSIC / BUILD ORDER

1. Do not hardware-test R189A.
2. Deep-audit the RTB `sound.cpk`/`movie1.cpk` registry and `spcload` relationships.
3. Obtain/locate a clean Storm 4 Switch registry baseline if possible and diff it against the AIO tables to identify exact new-slot records.
4. In Connections, test native CPK carrier precedence with a tiny controlled sentinel rather than a 1+ GiB aggregate.
5. Keep the current combined `Tobi_Switch.cpk` (`fb7ca9...d5488`) as the compact source-of-truth; do not duplicate it into full clean native CPKs.
6. Keep the minimal generic character-expander problem separate from resource transport.
7. Only after carrier behavior is proven decide between:
   - native carrier + minimal expander; or
   - external combined CPK + tiny generic mount/expander runtime.

---

## 9. STATUS

`RTB_SWITCH_EXE_HOOK_FOUND=NO`

`RTB_NATIVE_CPK_CARRIER_MODEL=CONFIRMED`

`RTB_MULTI_TABLE_NEW_SLOT_DATA=CONFIRMED`

`RTB_UNLIMITED_NUMERIC_EXPANSION=NOT_PROVEN`

`R189A_HARDWARE_TEST=RETIRED`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R190 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R190 FULL
## CURRENT FRONTIER — R189A NATIVE COMBINED BUILD PASS / HARDWARE TEST PENDING

> **Authoritative current section.** R190 records successful construction of the R189A native-CPK combined four-character package. This is a static/build PASS only. No hardware PASS is claimed yet. R184 remains frozen/pending and is not superseded by this branch.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

Every project update must preserve the complete previous FULL checkpoint verbatim below the new authoritative section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical.

---

## 1. R189A INPUT GATES — PASS

User executed the R189A builder in Termux.

Verified inputs:

```text
DONOR  fb7ca9a66cf7c0f4ee83ac1e1fc16e29ebbe130cfc7e2f6788c7ba39553d5488
COMMON a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27
MAIN   d008d651f6bf7ef2397b1b2a69e5d484210646c5327300ac277e2868b6769a7f
SOUND  ec0e21c08f31d45a6e4efe902e2303609f4e03c39961f37f4560e884cefc4694
```

Marker:

`INPUT_GATES=PASS`

---

## 2. CLEAN NATIVE CPK EXTRACTION — PASS

Clean v1.70 native archives extracted successfully:

- `patch/170/common.cpk`: 728 files
- `patch/170/sound.cpk`: 295 files

The previously validated combined donor overlay was then applied:
- common overlay: 222 files
- sound overlay: 26 files
- non-runtime/backup exclusions: 5 files
- donor `StageInfo.bin.xfbin` remains excluded/frozen

---

## 3. R189A NATIVE CPK REPACK — PASS

Generated native `common.cpk`:

```text
Mode      1
Files     925
Alignment 2048
Version   CPKMC2.30.07, DLL3.00.07
SHA256    2259e0fbfa4a358df841b9688526510ae51ae8ea895bc82edae132c54aed6236
```

Generated native `sound.cpk`:

```text
Mode      1
Files     318
Alignment 2048
Version   CPKMC2.30.07, DLL3.00.07
SHA256    c79f89c01f24a97086b861320325aa575cb574c001c62dfd1f5cc513ed438c3f
```

Marker:

`CPK_GATES=PASS`

Important: this proves pack/build structure only. It does not yet prove native runtime lookup behavior on hardware.

---

## 4. EXECUTABLE / RUNTIME CONTRACT

R189A uses the exact archived R185 character-expander `main` control:

```text
SHA256 d008d651f6bf7ef2397b1b2a69e5d484210646c5327300ac277e2868b6769a7f
```

This keeps the executable variable frozen while testing only native CPK ownership.

R189A intentionally contains:
- `exefs/main` = exact R185 expander control
- native `patch/170/common.cpk`
- native `patch/170/sound.cpk`
- loose known-good early `charicon_s.gfx`

R189A intentionally does NOT contain:
- `exefs/subsdk9`
- `romfs/data/moddingapi/Tobi_Switch.cpk`
- generic ModPack external CPK
- new CPK bind hook

Markers:

`NO_SUBSDK9=PASS`

`NO_EXTERNAL_CPK=PASS`

---

## 5. FINAL R189A PACKAGE — BUILD PASS

Output:

`$HOME/NSC2Switch_R189A_NATIVE_COMBINED_NO_SUBSDK9.zip`

Observed size: approximately 1.2 GiB.

SHA256:

```text
0ede90798da1bd3506b60b28987dedd28f92b0a71bd79470d0b33e9e9e2174d4
```

Marker:

`R189A_BUILD=PASS`

This is a **build/static PASS only**.

---

## 6. REQUIRED HARDWARE TEST — R189A

Deploy R189A with no leftover `subsdk9` and no external ModdingAPI CPK.

Test order:
1. cold boot;
2. Isshiki sanity test;
3. Tobi: slot/icon -> preview -> select -> VS -> battle entry/control;
4. Toneri: slot/icon -> preview -> select -> VS -> battle entry/control;
5. Itachi Storm 1: slot/icon -> preview -> select -> VS -> battle entry/control;
6. only after base entry/control passes, note obvious moveset regressions separately.

Do not use awakening/UJ/StageMove as the first acceptance criterion for R189A. Those belong to later gameplay-runtime layers.

Decision:
- all four baseline paths PASS -> native CPK ownership is sufficient for baseline four-character loading without `subsdk9`/external CPK bridge; proceed to R189B minimal clean-main expander;
- roster/icon visible but preview fails -> inspect native resource path registration/lookup and early resource ownership;
- preview passes but VS/battle fails -> inspect resolver/data/battle expander coverage and native resource ownership;
- Isshiki alone regresses -> inspect shared/global/sound overwrite semantics.

---

## 7. FROZEN STATE

Do not reinterpret or alter:
- R184 A/B: frozen/pending;
- R164 StageInfo: hardware PASS/frozen;
- R172 UJ: hardware PASS/frozen;
- P128 admission/session: frozen;
- voice state: frozen;
- D-pad historical state;
- no character-ID-specific production policy.

---

## 8. STATUS

`R189_DONOR_SPLIT=PASS`

`R189A_NATIVE_CPK_BUILD=PASS`

`R189A_HARDWARE=PENDING`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R189 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R189 FULL
## CURRENT FRONTIER — NATIVE CPK TRANSPLANT / COMBINED FOUR-CHARACTER DONOR

> **Authoritative current section.** R189 does not close or overwrite the frozen R184 A/B question. It opens a separate native-CPK research branch using the user's current combined four-character `Tobi_Switch.cpk` as donor and removes the external ModdingAPI CPK bridge from the next hardware probe.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

Every project update must preserve the entire preceding FULL checkpoint verbatim beneath the new authoritative section. The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical.

---

## 1. R184 CONTROL BRANCH REMAINS FROZEN / PENDING

Do not rewrite the R184 conclusion.

R184 still asks only:

**Does removing the loose R181 `main` break existing ModdingAPI/new-slot behavior when `subsdk9` is otherwise identical?**

R184 remains pending hardware A/B. R189 is an orthogonal native-CPK experiment and must not be interpreted as an R184 result.

Keep frozen:
- exact R181 gameplay runtime logic;
- P128 admission/session state;
- R172 UJ hardware-PASS path;
- R164 StageInfo hardware-PASS state;
- current voice conclusion;
- D-pad known state;
- no P81/P89/P125/StageRegistry migration;
- no character-ID-specific final production policy.

---

## 2. R189 DONOR LOCK

User-local donor:

`/storage/emulated/0/ewe/romfs/data/moddingapi/Tobi_Switch.cpk`

Observed:
- size: **411,934,982 bytes**
- SHA256: **fb7ca9a66cf7c0f4ee83ac1e1fc16e29ebbe130cfc7e2f6788c7ba39553d5488**
- CPK mode: **1**
- files: **254**
- alignment: **512**
- tool version reported by `cpk-tool`: **CPKMC2.45.00, DLL3.15.00**

This is not byte-identical to the archived R185 golden CPK (`6fa8bac6...c7c0c`) but has the same total byte size and the same 254-file combined architecture. R189 therefore treats `fb7ca9...d5488` as the user's current combined source-of-truth, while the archived R185 package remains the control/reference.

Character ecosystem present:
- Isshiki `9ish`, native replacement ID276
- Tobi `mtob`, custom ID281
- Toneri `8tnr_lx`, custom ID282
- Itachi Storm 1 `1itc`, custom ID283 / PSP538

All four parent manifests are present:
- `data/spcload/mtobprm_load.bin.xfbin`
- `data/spcload/8tnr_lxprm_load.bin.xfbin`
- `data/spcload/9ishprm_load.bin.xfbin`
- `data/spcload/1itcprm_load.bin.xfbin`

---

## 3. R189 DONOR SPLIT — PASS

Executed in Termux workspace:

`$HOME/R189_NATIVE_WORK`

Result:
- extracted donor: **254/254**
- `common_overlay`: **222 files**
- `sound_overlay`: **26 files**
- excluded non-runtime/backup: **5 files**
- frozen `StageInfo`: skipped from transplant

Excluded:
- `data/spc/Itachi_S1/unused_a.xfbin`
- `data/spc/Itachi_S1/unused_b.xfbin`
- `data/spc/Itachi_S1/unused_c.xfbin`
- `data/spc/Itachi_S1/1itcprm.bin.xfbin.backup`
- `data/ui/flash/OTHER/charicon_s/charicon_s.bak`

Frozen/skipped:
- `data/stage/StageInfo.bin.xfbin`

Post-split resource census:
- `mtob`: 46
- `8tnr`: 79
- `1itc`: 17
- `9ish`: 21

Required parent manifests: **4/4 PASS**.

Required global-table presence check: **PASS**.

Marker:

`R189_DONOR_SPLIT=PASS`

---

## 4. IMPORTANT CORRECTION — CPK SORTED FIELD

Do not use the previous fixed-offset `dd skip=0x128` check against the combined CPK.

The observed bytes `18 8d` are not a valid decoded `Sorted` field for this serialized header layout. Do **not** patch byte `0x129` blindly.

Historical P33A still establishes the engineering lesson that generated `Sorted=1` CPK behavior caused custom child `FILE_OPEN` failures and that the `Sorted=0` control fixed the observed custom file opens. But the current combined donor's header must be parsed structurally rather than with a hard-coded byte offset.

---

## 5. CHARACTER EXPANDER CORRECTION

The archived R185 audit is a delta from R183 to R185, not a complete vanilla-to-R185 patch list.

For a clean-v1.70 minimal character-expander build, the known staged architecture is:
- core capacity/allocation/init: 3 words
- active `prm_load` enumeration: 1 word
- resolver consumers: 2 words
- secondary data consumers: 5 words
- battle consumers: 3 words

Total: **14 instruction words**.

Target combined fixture:
- maximum installed custom ID: **283**
- active endpoint: **284**
- scalable core capacity: **1024**

The archived R185 audit confirms max ID283, endpoint284, capacity1024, and an 11-word R183->R185 delta. Do not mistake those 11 words for the full patch from vanilla.

---

## 6. NEXT HARDWARE PROBE — R189A

R189A is deliberately conservative.

Purpose: prove whether the current four-character ecosystem can run from native game CPK ownership with no `subsdk9` and no external ModdingAPI CPK mount.

Use:
- user's current `fb7ca9...d5488` combined donor as source-of-truth;
- clean v1.70 `patch/170/common.cpk` as native global/resource base;
- clean v1.70 `patch/170/sound.cpk` as native sound base;
- known R185 character-expander `main` as the first executable control;
- known-good loose early UI `.gfx` overrides from the existing modpack when present.

Do not use:
- `exefs/subsdk9`
- `romfs/data/moddingapi/Tobi_Switch.cpk`
- generic `NSC2Switch_ModPack.cpk`
- a new CPK-bind hook
- a new gameplay hook
- R172/P128/StageInfo migration changes

R189A is not yet the final generic main architecture. If native CPK + known R185 expander main passes, R189B will replace that executable with a clean-vanilla + guarded 14-word minimal expander and compare behavior.

---

## 7. R189A DECISION MATRIX

- **R189A PASS**: external CPK bridge / `subsdk9` is not required for baseline custom-resource loading; proceed to R189B clean-vanilla + 14-word minimal expander.
- **Roster visible, preview fails**: inspect native CPK resource lookup/path registration and early UI/resource availability.
- **Preview passes, VS/battle fails**: focus resolver/data/battle expander coverage and native resource ownership.
- **Isshiki regresses while custom slots work**: compare sound/global-table transplant ownership and shared-record overwrite behavior.

---

## 8. STATUS

`R189_DONOR_SPLIT=PASS`

`R189A_NATIVE_CPK_BUILD=PENDING`

`R189A_HARDWARE=PENDING`

`R184_AB=FROZEN_PENDING`

---

# COMPLETE PRIOR MASTER HISTORY — R188 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R188 FULL
## CURRENT FRONTIER — ZERO-EXEFS NATIVE `common.cpk` NEW-NAMESPACE PROBE BUILT / STATIC VALIDATION PASS

> **Authoritative current section.** R188 records the first actual zero-ExeFS native-CPK new-slot probe built from the R185–R187 RTB research branch. R188 does not claim hardware PASS. The package uses only a rebuilt v1.70 `data/patch/170/common.cpk`, adds a stock Nanashi-derived clone under new CharacodeID 281 / namespace `rprb`, and intentionally ships no `main`, `subsdk0`, `subsdk9`, or external ModdingAPI CPK. R184 remains preserved as the existing runtime packaging control lineage.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

The dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must remain byte-identical. Preserve the complete prior recovery history below each new authoritative section.

---

## 1. R188 INPUT GATE — PASS

Canonical user-supplied inputs are now locally ingested and hash-verified:

```text
v1.70 romfs_real common.cpk
size   363755660
SHA256 a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27

base data/launch/movie1.cpk
size   36182528
SHA256 c1cd43af4b4d32c8b380a1d51cc61b0fcbb3d6237873161d07faf2a9d6e586f1
```

The two uploaded split parts reconstructed the clean v1.70 `common.cpk` byte-identically to the R187 hash gate.

---

## 2. NATIVE CPK STRUCTURE DISCOVERED FROM CLEAN BYTES

Clean base `movie1.cpk`:
- CPK mode 1;
- alignment 2048;
- exactly 1 entry;
- only `data/movie_sw/na_0000_000.usm`.

Clean v1.70 `common.cpk`:
- CPK mode 1;
- alignment 2048;
- 728 entries;
- owns the authoritative v1.70 global roster tables;
- also contains full `9nns` Nanashi resource payload and `data/spcload/9nnsprm_load.bin.xfbin`.

This changes the staging plan: Probe A can be run against native `patch/170/common.cpk` alone. The clean base `movie1.cpk` is retained untouched for Probe B only if early launch-mount registration is still required.

---

## 3. R188 PROBE IDENTITY

Diagnostic clone:
- CharacodeID: **281**;
- namespace: **`rprb`**;
- donor: native Nanashi **`9nns`**;
- roster: page **7**, slot **13**;
- no Tobi-specific gameplay semantics;
- no specialCond/UJ/D-pad acceptance criteria.

Purpose: isolate whether a truly new namespace/ID can traverse native roster + prm_load/resource registration with **zero ExeFS runtime**.

---

## 4. R188 STATIC BUILD RESULTS — PASS

Output `common.cpk`:

```text
SHA256 44d702e54807af4c1ec02188fa62e837db26a10b51e95558faaaaa222cfbaccf
Files   730
Mode    1
Align   2048
```

Validated merged counts:
- characode `280 -> 281`;
- playerSetting `454 -> 457`;
- characterSelect `352 -> 355`;
- player_icon `465 -> 468`;
- duelPlayer pages `280 -> 281`;
- skillCustomize `240 -> 241`;
- spSkillCustomize `173 -> 174`;
- spTypeSupport `80 -> 81`;
- supportAction `171 -> 172`;
- skillIndexSetting `228 -> 229`;
- supportSkillRecoverySpeed `176 -> 177`;
- privateCamera `280 -> 281`;
- costumeParam `1433 -> 1445`;
- costumeBreak `296 -> 299`;
- appearanceAnm `340 -> 346`;
- awakeAura `418 -> 430`.

New PSP allocation:
- `527` / `9nns00_000001`;
- `529` / `9nns02_000001`;
- `532` / `9nns01_000001`.

All new PSP rows use CharacodeID 281 and ReferenceCharacodeID 281. MainPSP_ID resolves to 527.

---

## 5. NEW NAMESPACE REGISTRATION PAYLOAD

R188 adds:

```text
data/spcload/rprbprm_load.bin.xfbin
data/ui/max/crsel/c/rprbcharsel.xfbin
```

`rprbprm_load`:
- 27 records;
- cloned from native `9nnsprm_load`;
- internal prm_load namespace metadata renamed to `rprb`;
- every dynamic `<code*>` file-name placeholder is replaced by an explicit proven `9nns` donor resource name;
- no `<code*>` placeholder remains.

Therefore a preview/VS failure cannot be attributed merely to an absent custom raw moveset asset. It becomes stronger evidence for the native ID281/new-namespace registration/enumeration boundary.

---

## 6. R188 DEPLOYMENT CONTRACT — ZERO EXEFS

Install only:

```text
atmosphere/contents/0100FA10190A0000/
  romfs/data/patch/170/common.cpk
```

Must be absent during this test:
- `exefs/main`;
- `exefs/subsdk0`;
- `exefs/subsdk9`;
- `romfs/data/moddingapi/Tobi_Switch.cpk`;
- `romfs/data/moddingapi/NSC2Switch_ModPack.cpk`;
- historical `romfs/data/patch/170/movie.cpk` experiments.

---

## 7. REQUIRED HARDWARE TEST

1. Cold boot.
2. Enter character select.
3. Page 7 / slot 13 must appear as the new diagnostic clone beside native Nanashi slot 12.
4. Hover slot 13.
5. Observe whether a 3D preview appears.
6. Select slot 13.
7. Select map.
8. Observe VS transition.
9. Confirm battle entry and control.
10. Save a full log from boot through result.

Decision:
- **slot + preview + VS + battle PASS**: base new-slot registration can be native/data-only; full ModdingAPI runtime is not fundamentally required for this layer.
- **slot visible, preview/VS FAIL**: global roster tables are native-consumed, but new namespace/ID281 registration remains blocked. Next isolate early `movie1.cpk` registration vs the known vanilla prm_load enumeration endpoint; do not resume a full ModdingAPI port.
- **slot absent**: inspect rebuilt `common.cpk` priority/ownership/compatibility first.
- **boot failure**: treat CPK rebuild compatibility as the immediate issue, not proof against native new-slot architecture.

---

## 8. FROZEN STATE PRESERVED

R188 does not alter the prior hardware conclusions for:
- R164 StageInfo;
- R172 UJ;
- P128 admission/session;
- voice frozen state;
- R181 D-pad history;
- R184 packaging A/B question.

No char281-specific production policy is adopted. ID281 is only the current diagnostic fixture.

---

# COMPLETE PREVIOUS MASTER CHECKPOINT — R187 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R187 FULL
## CURRENT FRONTIER — NATIVE CPK HASH GATE PASSED; CLEAN INPUT IDENTITIES FROZEN

> **Authoritative current section.** R187 records the exact size/SHA256 identities of the two clean native CPK inputs selected for `RTB_NATIVE_CPK_PROBE_A`, plus the comparison hashes for the previously modified/reconstructed `romfs_updated` control and the RTB reference `movie1.cpk`. No hardware verdict changes. R184 packaging A/B remains frozen/pending as the control lineage; R185/R186 RTB-native-CPK research remains the active parallel branch.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change, the dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical. Preserve the complete previous checkpoint/history below the new authoritative section.

---

## 1. R187 HASH/SIZE GATE — USER HARD EVIDENCE

User captured exact byte sizes and SHA256 values in Termux.

### Selected clean/native probe inputs

```text
UPDATE v1.70 CLEAN / canonical source
path: /storage/emulated/0/Download/SWITCH/GAME/.nsc_uj_extract/update170/romfs_real/data/patch/170/common.cpk
size: 363755660 bytes
sha256: a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27
staging: $HOME/NSC_RTB_NATIVE_PROBE_INPUTS/NSC170_common_clean.cpk

BASE Connections CLEAN / early native-mount source
path: /storage/emulated/0/Download/SWITCH/GAME/.nsc_uj_extract/base/romfs_nca/data/launch/movie1.cpk
size: 36182528 bytes
sha256: c1cd43af4b4d32c8b380a1d51cc61b0fcbb3d6237873161d07faf2a9d6e586f1
staging: $HOME/NSC_RTB_NATIVE_PROBE_INPUTS/NSC_base_movie1_clean.cpk
```

### Comparison/control identities

```text
UPDATE v1.70 romfs_updated control
path: /storage/emulated/0/Download/SWITCH/GAME/.nsc_uj_extract/update170/romfs_updated/data/patch/170/common.cpk
size: 363755660 bytes
sha256: caa7ff29d6083f7e3cd08c3777cdf9fe278dff75299e7e15fbb70f571fd29b06

RTB modpack movie1 reference
path: /storage/emulated/0/Download/010084D00CF5E000/Mod/romfs/data/launch/movie1.cpk
size: 1350480 bytes
sha256: 208d2b4b7f59d7863e39018162e349a0d01a4039f64f6b4fb4df14ce82fc83f2
```

The RTB reference SHA256 matches the previously parsed R185 forensic artifact.

---

## 2. DECISIVE CLEAN-SOURCE RESULT

`romfs_real/data/patch/170/common.cpk` and `romfs_updated/data/patch/170/common.cpk` have the **same byte size** (`363755660`) but **different SHA256 hashes**.

Observed comparison:

```text
COMMON_REAL_UPDATED_IDENTICAL=NO
```

Therefore:
- `romfs_updated` is not byte-identical to the clean update extraction;
- it must remain a comparison/control only;
- all R187/R188 native-CPK reconstruction must use the exact `romfs_real` hash `a4fb86d7...` as the v1.70 source-of-truth;
- do not merge from or rebuild on top of `romfs_updated` until its delta has been separately audited.

This strengthens, rather than weakens, the R186 source-selection rule.

---

## 3. BASE `movie1.cpk` VS RTB REPLACEMENT — IMPORTANT SIZE FACT

Connections clean base `movie1.cpk` is `36,182,528` bytes, while the RTB modpack reference `movie1.cpk` is only `1,350,480` bytes.

Therefore the RTB Switch pack's tiny `movie1.cpk` is a purpose-built mod replacement/delta for Storm 4 and must **not** be copied directly onto Connections.

For Connections the probe must preserve all required native base `movie1.cpk` content while adding only the early-registration resources proven necessary by the diff. This remains a rebuild/merge problem, not a rename/copy problem.

---

## 4. R187 INPUT STATUS

```text
NSC170_common_clean.cpk
  FOUND: yes
  HASHED: yes
  STAGED: yes
  BYTES INGESTED BY CHATGPT: no

NSC_base_movie1_clean.cpk
  FOUND: yes
  HASHED: yes
  STAGED: yes
  BYTES INGESTED BY CHATGPT: no
```

The next technical operation requires the actual staged file bytes, not only their hashes.

---

## 5. NEXT FRONTIER — R188 CPK INGESTION / STRUCTURAL DIFF

Once the two staged clean files are uploaded, perform in this order:

1. verify uploaded sizes and SHA256 against R187 identities;
2. parse CPK headers/TOCs without modifying either input;
3. enumerate full `common.cpk` and `movie1.cpk` ownership;
4. extract only roster/resource-registration candidates first;
5. compare against the RTB two-tier architecture and historical NSC custom-character payload;
6. determine the minimum early-mount `prm_load`/namespace payload and latest-patch global table set;
7. rebuild candidate CPKs from copies only;
8. produce `RTB_NATIVE_CPK_PROBE_A` with **zero ExeFS**;
9. hardware acceptance remains `slot -> preview -> VS -> battle` before any Tobi-specific UJ/D-pad work.

Do not modify R184 A/B controls.

---

# COMPLETE PRIOR MASTER HISTORY — R186 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R186 FULL
## CURRENT FRONTIER — NATIVE CPK INPUTS LOCATED ON USER DEVICE; RTB PROBE MATERIAL ACQUISITION

> **Authoritative current section.** R186 records new user-supplied filesystem evidence locating the two exact clean/native CPK inputs required by R185's `RTB_NATIVE_CPK_PROBE_A`. No hardware verdict changes. R184 packaging A/B remains frozen/pending as the control lineage, and the R185 RTB-native-CPK hypothesis remains the active research branch.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change, the dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical. Preserve the complete previous checkpoint/history below the new authoritative section.

---

## 1. R186 NEW EVIDENCE — REQUIRED RAW CPK FILES LOCATED

User ran a recursive filesystem search on Android/Termux and located the required clean CPK sources.

Use these exact source paths for the probe:

```text
UPDATE v1.70 authoritative source:
/storage/emulated/0/Download/SWITCH/GAME/.nsc_uj_extract/update170/romfs_real/data/patch/170/common.cpk

BASE-game early native mount source:
/storage/emulated/0/Download/SWITCH/GAME/.nsc_uj_extract/base/romfs_nca/data/launch/movie1.cpk
```

Also present but **not** selected as the canonical clean inputs:

```text
/storage/emulated/0/Download/SWITCH/GAME/.nsc_uj_extract/update170/romfs_updated/data/patch/170/common.cpk
/storage/emulated/0/Download/010084D00CF5E000/Mod/romfs/data/launch/movie1.cpk
```

Reason:
- `romfs_real` is the clean update extraction and must be used instead of `romfs_updated`, which may contain previously modified/reconstructed state.
- `/Download/010084D00CF5E000/Mod/.../movie1.cpk` is the RTB modpack reference and must not be mistaken for the clean Connections base `movie1.cpk`.

No byte-level identity claim is made yet until hashes/sizes are captured.

---

## 2. REQUIRED ACQUISITION / HASH GATE

Before rebuilding either CPK, capture SHA256 and size for:
1. clean `romfs_real` v1.70 `common.cpk`;
2. `romfs_updated` v1.70 `common.cpk` as a comparison/control;
3. clean base Connections `movie1.cpk`;
4. RTB modpack `movie1.cpk` as a reference/control.

Do not overwrite or edit the originals in place. Copy the two selected clean inputs to a staging folder first.

Expected staging names:

```text
NSC170_common_clean.cpk
NSC_base_movie1_clean.cpk
```

---

## 3. R186 NEXT ACTION

User should upload the two staged clean CPK files (or a split archive containing them) so R187 can:
- parse both CPK TOCs;
- confirm native mount ownership/order;
- extract and diff the relevant roster/resource-registration tables;
- build `RTB_NATIVE_CPK_PROBE_A` with **zero ExeFS**;
- preserve R184/R185 controls untouched.

No runtime source should be modified before this CPK ingestion/diff is complete.

---

# COMPLETE PRIOR MASTER HISTORY — R185 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-03 R185 FULL
## CURRENT FRONTIER — RTB NATIVE-CPK RESEARCH BRANCH; R184 PACKAGING A/B REMAINS FROZEN/PENDING

> **Authoritative current section.** R185 records a new evidence-backed architecture branch discovered by forensic analysis of the user's NARUTO SHIPPUDEN: Ultimate Ninja STORM 4 Road to Boruto Switch modpack. It does **not** overturn the R184 hardware question and does **not** claim a new Connections hardware PASS. The existing R184 A/B remains the required control for the current ModdingAPI/runtime lineage. R185 adds a separate data-only/native-CPK experiment whose purpose is to determine whether the base new-slot/resource-registration layer can be moved out of `main`/`subsdk9` entirely.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change, the dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical. The complete previous checkpoint/history must remain preserved below the new authoritative section. No source, resolver, build, packaging, hardware conclusion, retired hypothesis, test result, or recovery-procedure change may be released without updating this file.

R185 discipline:
- R184 A/B is not silently replaced or skipped;
- no R184 frozen gameplay conclusion is reopened by this research alone;
- the RTB-native-CPK path is a **parallel experimental branch** until hardware proves it;
- no production package may be called data-only/new-slot-safe before the native-mount probe reaches battle on hardware/emulator.

---

## 1. R185 TRIGGER

User supplied/identified the archived Storm 4 RTB Switch modpack under Title ID `010084D00CF5E000` as a split ZIP:

```text
010084D00CF5E000.z01 ... 010084D00CF5E000.z15
010084D00CF5E000.zip
```

The archive was materialized and inspected directly. The goal was to answer whether its many added/new character slots depend on a Switch executable/runtime patch equivalent to PC ModdingAPI, and whether the same architecture can reduce or eliminate the NSC2Switch ModdingAPI runtime dependency.

---

## 2. RTB OUTER PACKAGE — DECISIVE FORENSIC RESULT

The RTB Switch modpack outer archive contains only `Mod/romfs/...` content. Relevant entries include:

```text
Mod/romfs/data/launch/movie1.cpk                 1,350,480 bytes
Mod/romfs/data/patch/3/sound.cpk             3,395,027,792 bytes
Mod/romfs/data/ui/flash/OTHER/charicon_s/charicon_s.gfx
Mod/romfs/data/ui/flash/OTHER/charsel/charsel.gfx
Mod/romfs/data/ui/flash/OTHER/...font GFX files
```

Observed absence:
- no `exefs/main`;
- no `subsdk*`;
- no IPS/executable patch payload;
- no custom Switch runtime loader.

**R185 conclusion A — HARD FORENSIC FACT:** this specific RTB Switch AIO/new-slot pack is deployed as RomFS/data overrides only. Its visible added roster does not require a packaged Switch `main`, `subsdk`, or IPS patch.

This does **not** prove unlimited character expansion on Switch. PC Storm 4 ModdingAPI still has a separate character-limit-expander feature; the forensic result proves only that this large RTB pack can expose its added roster without shipping an executable patch.

---

## 3. RTB `movie1.cpk` — SMALL HIGH-PRIORITY DELTA

Parsed CRI CPK metadata:
- size: `1,350,480` bytes;
- SHA256: `208d2b4b7f59d7863e39018162e349a0d01a4039f64f6b4fb4df14ce82fc83f2`;
- `Files = 10`;
- `Align = 512`;
- `Version = 7`, `Revision = 14`.

TOC contents:

```text
duel/unlockCharaTotal.bin.xfbin
duel/WIN64/unlockCharaTotal.bin.xfbin
spc/1tmrprm.bin.xfbin
spc/1tmrultreplace.xfbin
spc/1tmrultreplace2.xfbin
spc/1tmrultwep.xfbin
spc/9tmracc1.xfbin
spc/afterAttachObject.xfbin
spc/WIN64/afterAttachObject.xfbin
spcload/1tmrprm_load.bin.xfbin
```

ETOC `LocalDir` contains the source path:

```text
E:/New folder (2)/CrownClownAnimeAndGaming Mod Pack/data_win32
```

This is strong provenance that the Switch pack is a CPK/data port of a PC modpack rather than a Switch-native executable mod.

---

## 4. RTB `sound.cpk` IS ACTUALLY THE FULL AIO DATA CONTAINER

The split ZIP's giant `sound.cpk` was streamed/decompressed without extracting the full archive to disk. Parsed CPK metadata:
- uncompressed CPK size: `3,395,027,792` bytes;
- `Files = 5,380`;
- `ContentOffset = 2048`;
- `TocOffset = 3,394,718,208`;
- `EtocOffset = 3,394,961,920`;
- `Align = 512`;
- CPK tool version string: `CPKMG2.40.13, DLL3.24.00`.

The archive is not audio-only. Its 5,380 entries cover:
- `data/spc`;
- `data/spcload`;
- `data/duel`;
- `data/ui/max/select`;
- `data/ui/max/crsel/c`;
- `data/ui/flash/OTHER/charicon_p`;
- sound, stage, effect and other resource families.

Canonical registry/select files found and extracted:

```text
data/duel/unlockCharaTotal.bin.xfbin
data/spc/duelPlayerParam.xfbin
data/spc/playerSettingParam.bin.xfbin
data/spc/skillCustomizeParam.xfbin
data/spc/spTypeSupportParam.xfbin
data/ui/max/select/characterSelectParam.xfbin
```

Observed decompressed sizes:

```text
unlockCharaTotal.bin.xfbin       4,292
duelPlayerParam.xfbin          194,192
playerSettingParam.bin.xfbin    50,416
characterSelectParam.xfbin     111,780
skillCustomizeParam.xfbin       85,136
spTypeSupportParam.xfbin        14,976
```

`duelPlayerParam.xfbin` contains 217 unique `*prm_bas.bin` source-name codes in this pack. This count is a resource-definition census, **not** asserted as 217 independently playable roster slots.

`playerSettingParam.bin.xfbin` contains the expected characode/preset/message mappings; `characterSelectParam.xfbin` is the roster/select table; `unlockCharaTotal.bin.xfbin` is an explicit unlock/playability dataset.

**R185 conclusion B:** Storm 4 RTB AIO new-slot behavior is a multi-table, multi-resource system. It is not merely a `characterSelectParam` edit and not merely an icon GFX edit.

---

## 5. RTB SWITCH PACKAGING MODEL

The observed RTB architecture is effectively two-tier:

```text
native early/base CPK slot:
  data/launch/movie1.cpk
    -> small high-priority delta / unlock + character-specific data

native patch CPK slot:
  data/patch/3/sound.cpk
    -> large AIO registry + resource container

loose LayeredFS UI overrides:
  charicon_s.gfx
  charsel.gfx
  related GFX/font files
```

Community reports independently describe the same Switch porting pattern: build a PC-style data CPK as `movie1.cpk` under `romfs/data/launch`, rename PC `WIN64` folders to `SWITCH`, and for Ultimate AIO use the Switch patch folder (`3`) and replace `sound.cpk`.

Source:
- GBAtemp, “Naruto Ultimate Ninja Storm 4 Modding”: https://gbatemp.net/threads/naruto-ultimate-ninja-storm-4-modding.563665/

---

## 6. IMPORTANT LIMIT — STORM 4 PC API STILL HAS A SEPARATE LIMIT EXPANDER

The public Storm 4 ModdingAPI README documents a separate “character limit expander” and advertises adding up to 65,535 characters on PC. Therefore:
- do **not** infer that the Switch data-only pack has no native hard limits at all;
- do **not** infer that arbitrary IDs/counts are unlimited;
- do distinguish “a large AIO roster works data-only on Switch” from “the PC API's maximum-range expansion has been ported.”

Source:
- Perfect-Storm / Storm 4 ModdingAPI: https://github.com/exavadw/Perfect-Storm

---

## 7. CONNECTIONS HAS DIRECT HOMOLOGS OF THE RTB REGISTRY TABLES

Inspection of the historical Connections `movie.cpk` oracle in Library confirms these native NSC data names exist:

```text
characode.bin.xfbin
duelPlayerParam.xfbin
playerSettingParam.bin.xfbin
player_icon.xfbin
characterSelectParam.xfbin
skillCustomizeParam.xfbin
spSkillCustomizeParam.xfbin
spTypeSupportParam.xfbin
costumeParam.bin.xfbin
```

Current PC Connections Mod Manager also explicitly supports character mods that replace/add characters and a Character Roster Editor. Current UltimateStormAPI release history adds Connections-specific `charRelationParam.xfbin`, confirming that Connections shares the broad data-driven roster architecture but has additional/changed schema.

Sources:
- https://github.com/TheLeonX/NSC-ModManager
- https://github.com/TheLeonX/NSC-ModManager/releases

**R185 conclusion C:** direct RTB binary-copy is not justified, but the architectural concept is strongly transferable because Connections retains homologous registry/select datasets.

---

## 8. CONNECTIONS UPDATE 1.70 NATIVE CPK OWNERSHIP — CRITICAL DIFFERENCE

Saved v1.70 inventory proves the latest global roster/parameter versions are in:

```text
data/patch/170/common.cpk
```

The 1.70 `common.cpk` contains at least:

```text
appearanceAnm
characterSelectParam
conditionprm.bin.xfbin
costumeBreakParam
costumeParam
duelPlayerParam
messageInfo.bin.xfbin
player_icon
playerSettingParam
privateCamera
skillCustomizeParam
skillIndexSettingParam
spSkillCustomizeParam
spTypeSupportParam
supportActionParam
```

`data/patch/170/sound.cpk` is also present but the saved global-param census only identifies `cmnparam` there.

Base Connections also has:

```text
data/launch/movie1.cpk
```

but the saved base scan identifies only its movie `.usm` payload, not roster params.

**R185 conclusion D:** the closest native-mount analog to RTB cannot simply be assumed to be `launch/movie1.cpk`. In Connections v1.70, the authoritative/latest roster tables are owned by `patch/170/common.cpk`.

---

## 9. WHY THE OLD `patch/170/movie.cpk` TEST DOES NOT DISPROVE THE NEW IDEA

Historical NSC2Switch P17/P20 experiments already tried moving a **partial** custom payload to:

```text
data/patch/170/movie.cpk
```

and did not restore Tobi preview/battle by itself. This remains valid negative evidence.

However the RTB forensic result changes the interpretation:
1. RTB AIO uses a complete multi-table/resource ecosystem, not a ~single-character partial delta alone.
2. Connections v1.70 latest roster tables are actually sourced from `patch/170/common.cpk`, not an existing `patch/170/movie.cpk`.
3. Historical P27A proved a crucial distinction: custom numeric ID281 and PSP IDs 527+ were valid enough for selection/preview/VS/battle when ID281's characode string was redirected from the genuinely new namespace `mtob` to vanilla namespace `1nrt`.
4. Therefore the hard blocker was tied to new **resource namespace / prm_load registration**, not the mere existence of a roster slot or custom numeric ID.

This lines up directly with the RTB hypothesis: a native CPK that is already mounted before one-shot character-resource registration may remove the need for the late custom CPK bind/runtime bridge.

---

## 10. R185 NEW ARCHITECTURE HYPOTHESIS — TWO-TIER NATIVE CPK, ZERO EXEFS FOR BASE NEW-SLOT

The most promising data-only Connections design is now:

```text
Tier A — EARLY native mount
  data/launch/movie1.cpk (rebuilt while preserving original movie content)
    -> custom <characode>prm_load.bin.xfbin
    -> custom character resource namespace/assets needed before registration

Tier B — LATEST v1.70 patch ownership
  data/patch/170/common.cpk (rebuilt from the exact v1.70 original)
    -> merged characode
    -> merged duelPlayerParam
    -> merged playerSettingParam
    -> merged player_icon
    -> merged characterSelectParam
    -> other required global tables

Loose LayeredFS UI, if required
  data/ui/flash/OTHER/charicon_s/charicon_s.gfx
  other exact UI registrations

ExeFS for base-slot probe
  NONE
```

The purpose is not to reproduce every UltimateStormAPI gameplay feature. The first target is narrower:

**Can a truly new characode namespace be registered early enough by native CPK mounts to reach preview/VS/battle with original v1.70 `main` and no `subsdk9`?**

If yes, NSC2Switch can split architecture:
- base character/new-slot registration = RomFS/data-only;
- only features proven impossible in data = small optional runtime compatibility layer;
- full PC ModdingAPI port is no longer the default requirement.

---

## 11. REQUIRED FILES FOR THE DECISIVE NATIVE-CPK PROBE

The Library does **not** currently contain raw standalone copies of:

```text
v1.70 update: data/patch/170/common.cpk
base game:     data/launch/movie1.cpk
```

Saved reports prove both existed in the user's dump, but the CPK bytes themselves are not retained in Library.

Do not fabricate a definitive probe by relabeling the historical 388,461,408-byte `movie.cpk` oracle as `common.cpk`; prior architecture rules explicitly treat that file as an oracle/reference, not a production base.

Needed next inputs from the user's existing Switch dump:
1. exact v1.70 `data/patch/170/common.cpk`;
2. exact base `data/launch/movie1.cpk`.

Optional but useful for completeness:
3. exact v1.70 `data/patch/170/sound.cpk`.

---

## 12. DECISIVE HARDWARE TEST PLAN — `RTB_NATIVE_CPK_PROBE_A`

Keep R184 A/B untouched. Build/test this as a separate clean deployment.

### Phase 1 — one-character clone/control
Use one known stock character resource set first, but allocate it through a new roster record/ID. This tests registration architecture without Tobi-specific UJ/stage/D-pad complexity.

Required deployment:

```text
atmosphere/contents/0100FA10190A0000/
  romfs/data/launch/movie1.cpk
  romfs/data/patch/170/common.cpk
  [required loose UI GFX]
```

Explicitly absent:

```text
exefs/main
exefs/subsdk0
exefs/subsdk9
romfs/data/moddingapi/Tobi_Switch.cpk
```

### Acceptance order
1. cold boot;
2. character select renders;
3. new slot/icon exists;
4. hover -> 3D preview;
5. select character;
6. select map;
7. VS transition;
8. battle enters and actor is controllable.

### Interpretation
- **slot + preview + VS/battle PASS**: native data path is sufficient for base new-slot registration; custom CPK bridge/character-expander runtime is not fundamentally required for that layer.
- **slot visible, preview FAIL**: roster tables are accepted but custom resource namespace/prm_load still misses registration; compare mount order and early `prm_load` visibility before adding executable patches.
- **preview PASS, VS FAIL**: selection-side registration is solved; isolate battle-only consumer tables/registration.
- **slot absent**: latest global params are not winning; inspect CPK priority/mount ownership and UI registration.
- **boot/regression**: rebuild/merge completeness issue first; do not infer native expansion is impossible.

Only after a stock clone passes should the probe use real `mtob`, then Toneri/Itachi/etc.

---

## 13. RELATION TO R184 — NO CONFLICT / NO SILENT VERDICT CHANGE

R184 remains the authoritative control for the existing runtime architecture:
- exact R181 gameplay runtime logic;
- identical `subsdk9` A/B;
- presence/absence of loose `main` as the isolated variable;
- P81/P89/P125/StageRegistry migration frozen.

R185 does **not** reinterpret an untested R184 result.

Instead, R185 establishes a parallel architecture question:

> Can the new-slot/resource-registration layer be made native/data-only by moving the full required registry + custom resource namespace into CPKs that the game itself mounts before registration?

If this passes, future ModdingAPI work should be reduced to only the remaining runtime-only behavior (if any), rather than treating the full PC API as mandatory infrastructure.

---

## 14. R185 STATUS

### Forensic/research verification
- RTB split archive complete: PASS
- RTB outer package has no ExeFS/IPS: PASS
- RTB `movie1.cpk` parsed: PASS
- RTB giant `sound.cpk` streamed and TOC parsed: PASS
- RTB full-container file count 5,380: PASS
- RTB core roster tables extracted/decompressed: PASS
- Connections homologous parameter names confirmed: PASS
- Connections v1.70 `patch/170/common.cpk` ownership confirmed from saved inventory: PASS
- old NSC partial `patch/170/movie.cpk` negative result preserved: PASS
- R184 runtime verdict changed: **NO**
- RTB-native-CPK Connections hardware test: **NOT YET RUN**

### Current next action
Obtain the exact raw v1.70 `data/patch/170/common.cpk` and base `data/launch/movie1.cpk`, then build `RTB_NATIVE_CPK_PROBE_A` as a zero-ExeFS, one-new-slot registration test. Do not modify R184's A/B packages while doing so.

---

# COMPLETE PREVIOUS MASTER CHECKPOINT — R184 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-02 R184 FULL
## CURRENT FRONTIER — R181-EXACT PACKAGING A/B AFTER R183 HARDWARE FAIL

> **Authoritative current section.** R184 supersedes R183 for diagnosis only. R183 hardware result is unchanged from R182: new/custom character still stalls at the VS screen and several Isshiki functions remain non-functional. Because R183 had already restored the gameplay/content-sensitive R182 changes to R181 behavior, R184 removes the remaining source-layout refactor too and isolates the loose `main` packaging variable with one identical `subsdk9` build.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change, the dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical. The complete prior recovery history must remain preserved inside the new FULL checkpoint. No source, resolver, build, packaging, hardware conclusion, retired hypothesis, test result, or recovery-procedure change may be released without updating this file.

---

## 1. R184 TRIGGER / NEW HARDWARE EVIDENCE

Hardware report for R183:
- result is **the same as R182**;
- new/custom character still becomes stuck at the VS screen;
- Isshiki still has multiple functions that do not work.

Immediate conclusion:
- the R182 resolver migration alone is not the root cause;
- the R182 generic ModPack-path experiment alone is not the root cause;
- R183 restored those gameplay/content-sensitive paths to R181 but retained two Phase1 deltas: the `main.cpp -> nsc_runtime_core` source split and bootstrap-only/no-loose-main packaging;
- therefore the next test must isolate those remaining variables without touching gameplay logic.

No new D-pad, P128, voice, stage, or UJ conclusion is taken from this report.

---

## 2. R184 SOURCE POLICY — EXACT R181 RUNTIME SOURCE

R184 deliberately returns the compiled runtime source to the exact R181 baseline.

The following files are hash-locked to R181:
- `overlay/source/program/main.cpp`
  - SHA256 `974b67b3e2bc6cfee6755bc5fef130851e33f294598d1e0cd873a64c3ecc63df`
- `overlay/source/program/nsc_cpk_bridge.cpp`
  - SHA256 `c69d8d772db2d9f643e31bf4c424f983c546dbca5bdd6f34f7882542c3155480`
- `overlay/source/program/nsc_cpk_bridge.hpp`
  - SHA256 `c8b85c98622d3f2fd7cef065bb06dad35744e595e2dbe57e0796d0a76d0935bc`
- `overlay/source/program/nsc_runtime_v2.cpp`
  - SHA256 `7ad1bd3be39a1c70433264016b18dde5c02ee6ecb7943ea4ae09d949b9414248`
- `overlay/source/program/nsc_runtime_v2.hpp`
  - SHA256 `5c54f6db966351c3392684525da76dd23faec215071ed4274ee7bc928d41b153`
- `overlay/source/program/condition_compat_generated.hpp`
  - SHA256 `19d0f2deac6dbcaa0b3d64bc0eb8a28a8f8e0387c71e2343387a6c46788e9135`
- `overlay/source/program/nsc_sfx_list_generated.hpp`
  - SHA256 `62576a81e45f3e322aa43458801bbf41cb0e8e343738eee9095a6c49de092a92`
- `overlay/source/program/p81_ougi_awake_ids.hpp`
  - SHA256 `e16e36fdb3779a21914dab2065e919a9c870094b9f91e8d599176e6608e40cde`
- `prepare_exlaunch.sh`
  - SHA256 `8fbfe3d08d2dc64588db2f9ca53243b8369f2f3b14c857521e1dd813acc4883a`

R182/R183 source-layout split is **absent** in R184:
- no `nsc_runtime_core.cpp`;
- no `nsc_runtime_core.hpp`;
- R181 `main.cpp` directly performs the proven installer sequence again.

This means any hardware difference between R184 A and B cannot be attributed to the Phase1 translation-unit split.

---

## 3. R184 SINGLE-BUILD PACKAGING A/B

R184 builds `subsdk9` exactly once from the R181-exact source, then copies the same binary into both packages.

### A_WITH_MAIN — CONTROL
Contains:
- R181 original loose `main`;
- the newly built R184 `subsdk9`.

`main` SHA256 must be:
`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

This recreates the previous R181 deployment contract as closely as possible.

### B_NO_MAIN — ISOLATION
Contains:
- the exact same `subsdk9` binary as A;
- no loose `main`.

The workflow performs `cmp` on A/B `subsdk9` before artifact upload. Therefore the only intended variable is presence/absence of the loose `main` override.

---

## 4. REQUIRED HARDWARE TEST — EXACT ORDER

Precondition:
- restore/preserve the exact RomFS/CPK setup that was known-good before R182;
- do not mix ExeFS files from R182 or R183;
- fully close the game before switching variants.

### Test A — `A_WITH_MAIN`
1. Install A so title ExeFS contains both `main` and `subsdk9`.
2. Cold boot.
3. Select the new/custom character that currently stalls at VS.
4. Confirm whether VS transition reaches battle.
5. Test the exact Isshiki functions that became non-functional.
6. Save full runtime log from boot through the test battle.

### Test B — `B_NO_MAIN`
1. Fully close the game.
2. Remove only the loose SD `exefs/main` for this title.
3. Leave the identical R184 `subsdk9` installed.
4. Cold boot.
5. Repeat the same custom-character VS test and same Isshiki functions.
6. Save full runtime log.

Do not use D-pad behavior as the primary decision criterion for this A/B.

---

## 5. R184 DECISION TABLE

### A PASS / B FAIL
**No-loose-main packaging is the regression boundary.**

Consequence:
- freeze removal of `main`;
- retain R181 deployment with the known main while designing a loader/bootstrap architecture that can prove equivalent module/layout behavior before removing it;
- do not resume Phase2 resolver migration yet.

### A PASS / B PASS
**No-main packaging is safe.**

Consequence:
- the R182/R183 source-layout/refactor changed runtime behavior despite intended semantic equivalence;
- keep exact R181 entrypoint/source organization as the new architecture baseline;
- future decoupling must occur behind that proven binary/layout boundary.

### A FAIL / B FAIL
The regression is outside the isolated Phase1/no-main difference, or the deployed hardware state is stale/mixed.

Next action:
- compare the actual installed ExeFS/RomFS files and hashes against the last-known-good R181 deployment;
- verify that the built `subsdk9` corresponds to this source package;
- revalidate the exact CPK set used when Isshiki/new slots last worked.

### A FAIL / B PASS
Unexpected result. Treat as evidence of stale/mismatched loose `main` or mixed deployment. Do not make further runtime changes before file/hash reconciliation.

---

## 6. R184 VERIFICATION STATUS

Source verifier result:
- all R181 compiled source files hash-identical: PASS;
- Phase1 core split absent: PASS;
- original `main` hash: PASS;
- P128 reference hash: PASS;
- exact 30-word reference delta: PASS;
- R181 native gate fingerprint: PASS;
- R172 SetAnmDirect fingerprint: PASS;
- R175 action lookup fingerprint: PASS;
- StageRegistry fingerprint: PASS;
- single-build A/B packaging assertions: PASS;
- A contains main / B contains no main: PASS;
- dual A/B ZIP artifact definitions: PASS.

Marker:
`NSC_RUNTIME_R184_SOURCE_VERIFY=PASS`

---

## 7. LOCKED PROJECT STATE WHILE R184 IS UNDER TEST

Do **not** proceed with P81/P89/P125/StageRegistry resolver migration until R184 A/B identifies the regression boundary.

Keep frozen:
- exact R181 gameplay runtime logic;
- exact30 P128 plan;
- R172 UJ path;
- current voice state;
- current stage conclusions;
- D-pad known issues and retired hypotheses;
- no char281-specific final architecture;
- no generic ModPack-path rollout yet.

Primary question now is only:
**Does removing the loose R181 `main` break existing ModdingAPI/new-slot behavior when `subsdk9` is otherwise identical?**

---

# COMPLETE PRIOR MASTER HISTORY — R183 FULL PRESERVED VERBATIM BELOW

# NSC2Switch MASTER CHECKPOINT — 2026-10-02 R183 FULL
## CURRENT FRONTIER — MODDINGAPI COMPATIBILITY HOTFIX AFTER R182 HARDWARE REGRESSION

> **Authoritative current section.** R183 supersedes R182 for deployment. R182 hardware testing reported a new/custom-character VS-screen stall and partial Isshiki functionality loss. R183 keeps only the structural decoupling that does not change gameplay semantics and rolls gameplay/content-sensitive Phase 1 changes back to the exact R181 source behavior.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

For every future change, the dated FULL checkpoint and `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical, and the complete preceding history must remain embedded below the new authoritative section. No source, resolver, build, packaging, hardware conclusion, retired hypothesis, or recovery-procedure change may be released without updating this file.

---

## 1. R183 TRIGGER / HARDWARE VERDICT

R182 hardware report from user:
- new/custom character becomes stuck on the VS screen;
- Isshiki mod has several functions no longer working.

Decision:
- treat both as **R182 regressions** until disproven;
- do not continue Phase 2 resolver migration from the R182 runtime candidate;
- restore proven R181 behavior first, while retaining only architecture changes that do not alter runtime semantics.

No new D-pad conclusion is taken from this regression report.

---

## 2. ROOT-CAUSE PRIORITY

Most dangerous R182 change:
- `InstallR181DpadFullEligibilityRollback()` was changed from the proven fixed v1.70 two-word fingerprint at `main+0x59CEB4` to an 8-word unique signature scan.
- `nsc_runtime_core::Initialize()` treats R181 validation as mandatory and returns false on failure.
- therefore a resolver miss/ambiguity on hardware can abort initialization before later installers run, producing a plausible partial-runtime state: earlier patches active, later CPK/gameplay hooks absent.

Second compatibility risk:
- CPK mounting changed from the proven `sim:data/moddingapi/Tobi_Switch.cpk` path to generic `NSC2Switch_ModPack.cpk` primary + legacy fallback.
- because the user is testing an existing multi-character setup, content-loader semantics must remain frozen until compatibility is re-proven.

R172 resolver migration is also rolled back for this hotfix so R183 changes no proven gameplay-sensitive address semantics relative to R181.

---

## 3. R183 EXACT SOURCE DECISION

### Retained from R182
1. `main.cpp` remains a thin exlaunch bootstrap.
2. Runtime initialization remains behind stable C ABI:
   `extern "C" bool nsc_runtime_initialize();`
3. `nsc_runtime_core.cpp/.hpp` retains the exact R181 installer order.
4. GitHub Actions runtime artifact remains bootstrap-only and does **not** ship a loose game `main` override.

### Rolled back byte-for-byte to R181 behavior
1. **R181 gate validation**
   - fixed v1.70 offset `main+0x59CEB4`;
   - expected words `B94E5768 7101F11F`;
   - zero gate writes.
2. **R172 SetAnmDirect validation**
   - proven fixed v1.70 `kCentralActionSetterOffset` / `main+0x766320` fingerprint path;
   - no CentralSetter resolver dependency for this revision.
3. **ModdingAPI CPK bind path**
   - exact proven path `sim:data/moddingapi/Tobi_Switch.cpk`;
   - generic `NSC2Switch_ModPack.cpk` binding is deferred/retired from active deployment until a separate multi-pack design is hardware-tested.

Important: the large gameplay/runtime implementation files `nsc_runtime_v2.cpp` and `nsc_cpk_bridge.cpp` are restored to the original R181 source bytes for these affected paths. The architectural split lives outside them.

---

## 4. DEPLOYMENT CONTRACT FOR R183 TEST

Use the R183-built `subsdk9` as runtime bootstrap.

Do not add the R182 generic ModPack experiment for this A/B test. Preserve the exact pre-R182 RomFS/CPK setup that previously loaded Tobi/Isshiki/new slots.

R183 release package still intentionally contains no loose `exefs/main`. This is retained as the architecture experiment under test; if R183 still reproduces the VS-screen regression, the next A/B boundary is bootstrap-only/no-main packaging versus the previous R181 packaging contract.

---

## 5. REQUIRED HARDWARE TEST — MINIMAL DECISIVE ORDER

1. Cold boot / fully restart title.
2. Confirm title reaches menu.
3. Select the exact new/custom character that stalled on R182 and start battle.
   - PASS: leaves VS screen and reaches battle.
   - FAIL: still stalls; capture full log from launch through stall.
4. Test Isshiki specifically on the functions that stopped working in R182.
   - record each restored/still-broken function by name/action.
5. Test Tobi normal battle + UJ once to guard R172/P128 baseline.
6. Do not use D-pad results as the primary R183 verdict.

Decisive interpretation:
- new char + Isshiki recover on R183 => R182 gameplay/content-sensitive resolver/bind changes were the regression boundary; keep structural split and proceed with one migration at a time.
- regression remains on R183 => next test is R181 exact packaging versus R183 bootstrap-only packaging, because source gameplay paths are already restored.

---

## 6. NEXT DEVELOPMENT RULE

Do **not** migrate P81/P89/P125/StageRegistry yet.

First establish R183 hardware parity. After parity:
1. migrate exactly one dependency;
2. build;
3. update FULL checkpoint;
4. hardware test new-char VS + Isshiki + Tobi UJ;
5. only then migrate the next dependency.

Generic/multi-CPK ModdingAPI loading must be designed as an explicit multi-pack registry/enumeration layer, not by silently replacing the proven single CPK path.

---

## 7. R183 FILES / VERIFICATION

New/updated project files:
- `overlay/source/program/main.cpp` — thin bootstrap retained;
- `overlay/source/program/nsc_runtime_core.cpp/.hpp` — loader-neutral core retained;
- `overlay/source/program/nsc_runtime_v2.cpp` — R181 gameplay-sensitive gate behavior restored;
- `overlay/source/program/nsc_cpk_bridge.cpp` — R181 R172 + CPK bind behavior restored;
- `.github/workflows/build-runtime-r181.yml` — R183 artifact/verifier, bootstrap-only packaging;
- `prepare_exlaunch.sh` — R183 ELF label;
- `verify_runtime_r183.py` — R183 source/historical fingerprint verifier;
- `MODDINGAPI_R183_COMPAT_HOTFIX_REPORT.md` — regression/hotfix summary.

The source verifier must confirm:
- thin bootstrap/core ABI;
- exact installer order;
- R181 fixed gate behavior restored;
- R172 fixed fingerprint behavior restored;
- proven Tobi CPK bind path restored;
- no generic ModPack path active;
- no loose `main` in runtime artifact;
- exact original/P128 binary hashes and 30-word reference delta;
- FULL checkpoint/LATEST synchronization;
- R182 and R181 histories preserved below.

---

# PRESERVED PREVIOUS FULL CHECKPOINT

# NSC2Switch MASTER CHECKPOINT — 2026-10-02 R182 FULL
## CURRENT SOURCE/ARCHITECTURE FRONTIER — MODDINGAPI PHASE 1 DECOUPLING

> **Authoritative current section.** R182 is the current source/package checkpoint after the ModdingAPI Phase 1 refactor. The proven gameplay lineage through R181 is preserved in full below. R182 changes architecture/packaging and resolver usage; it does **not** silently replace hardware evidence from earlier revisions.

---

## 0. MANDATORY CHECKPOINT DISCIPLINE — FROZEN PROJECT RULE

**EVERY PROJECT UPDATE MUST UPDATE THIS FULL MASTER CHECKPOINT.**

This applies to every change, including:
- C/C++ runtime source changes;
- resolver/signature changes;
- hook install order changes;
- build/workflow changes;
- packaging/layout changes;
- ModdingAPI/CPK path changes;
- scripts/verifiers;
- hardware-test conclusions;
- retired hypotheses;
- documentation that changes the current recovery procedure.

Required behavior for every future update:
1. Create/update the dated `NSC2Switch_MASTER_CHECKPOINT_<DATE>_<REV>_FULL.md`.
2. `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` must be byte-identical to that current FULL checkpoint.
3. Preserve the previous full checkpoint/history below the new authoritative section; never replace it with a short delta-only changelog.
4. Record what changed, what did not change, validation status, hashes where relevant, and the exact next test/frontier.
5. Source/build verification must fail if the current FULL checkpoint and `LATEST` diverge.

The checkpoint is part of the release artifact, not optional documentation.

---

## 1. R182 SCOPE

R182 records the ModdingAPI Phase 1 architecture refactor requested after the R181 gameplay checkpoint.

Primary goal:
- stop coupling content-mod releases to a replaced game `main`;
- isolate the executable bootstrap from gameplay/runtime core initialization;
- reduce direct v1.70 absolute-address use on live runtime paths;
- make later game updates require resolver maintenance rather than rebuilding a patched `main` for every content mod.

This revision is a **source/architecture candidate**. Hardware gameplay baseline remains the previously proven/frozen states until this build is compiled and hardware-tested.

---

## 2. GAME / BASELINE IDENTITY — UNCHANGED

- Game: NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS Switch v1.70.
- Title ID: `0100FA10190A0000`.
- Build ID: `48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39`.
- Original `main` SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- Reference P128 `main` SHA256: `904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff`.
- Original submitted source package SHA256: `9447438755766675254f653c5b004738c29b13011f445a24d81cd0b7ac15405b` (`NSC2SwitchSC.zip`).
- Previous ModdingAPI Phase 1 package SHA256: `2ea0db2e585daef788737cefe053ed551d06d3e9e6cbde9abb71d3e784cc4c27`.
- Exact historical/reference runtime main delta remains 30 words = condition5 5 + P67 1 + P128 24.

Do not deploy the reference P128 `main` or any historical patched `main` as a current SD override.

---

## 3. FROZEN FUNCTIONAL / HARDWARE INVARIANTS

The architecture refactor does not reopen already-frozen gameplay conclusions:

- R164 StageInfo: hardware PASS/frozen.
- R172 UJ: hardware PASS/frozen; Tobi UJ no longer loops.
- P128 admission/session path: frozen unless new hardware evidence directly contradicts it.
- Voice: frozen/skipped by user.
- Final gameplay architecture remains generic: no char281-specific gameplay policy.
- R181 D-pad recovery state/history is preserved below exactly as the preceding checkpoint.

No new D-pad gameplay conclusion is claimed by R182 solely from source verification.

---

## 4. MODDINGAPI PHASE 1 — CURRENT IMPLEMENTATION

### 4.1 Game `main` is no longer a release payload
The GitHub Actions runtime package now emits only the runtime bootstrap under:

`runtime/atmosphere/contents/0100FA10190A0000/exefs/subsdk9`

The workflow explicitly asserts that no loose `exefs/main` is shipped.

The original and P128 `main` binaries remain in the source tree only as verification/fingerprint fixtures.

### 4.2 Bootstrap/core split
Runtime initialization was moved behind a stable loader-neutral C ABI:

`extern "C" bool nsc_runtime_initialize();`

Files:
- `overlay/source/program/nsc_runtime_core.hpp`
- `overlay/source/program/nsc_runtime_core.cpp`

`overlay/source/program/main.cpp` is now a thin exlaunch adapter that initializes exlaunch and calls the runtime-core ABI.

Current meaning of `subsdk9`:
- executable transport/bootstrap only;
- installed once for NSC2Switch runtime;
- not part of each character/content mod;
- not considered a gameplay-data dependency.

Important: physically deleting `subsdk9` now would prevent the runtime from entering the game process. A zero-`subsdk9` design requires a replacement loader/bootstrap that calls the same `nsc_runtime_initialize()` ABI.

### 4.3 Generic ModdingAPI CPK path
Preferred runtime CPK path:

`sim:data/moddingapi/NSC2Switch_ModPack.cpk`

Legacy fallback retained for compatibility:

`sim:data/moddingapi/Tobi_Switch.cpk`

New content packs should target the generic ModPack path. Character/content releases should be RomFS/data-only and should not ship their own `main` or `subsdk9`.

### 4.4 Resolver migration completed in Phase 1
Two active couplings were moved away from direct fixed-address use:

1. R172 `SetAnmDirect` obtains `CentralSetter` from `RuntimeResolver`.
2. R181 native D-pad eligibility gate is resolved by a unique native instruction signature rather than directly using `main+0x59CEB4`.

Both remain fail-closed when resolution is not valid.

---

## 5. CURRENT DEPLOYMENT CONTRACT

### Runtime — install once
```text
atmosphere/
└── contents/0100FA10190A0000/
    └── exefs/
        └── subsdk9
```

### Character/content mods — data only
```text
atmosphere/
└── contents/0100FA10190A0000/
    └── romfs/
        └── data/
            └── moddingapi/
                └── NSC2Switch_ModPack.cpk
```

Any required UI/icon files stay under their normal RomFS paths.

Release rule:
- content mod: **no `exefs/main`**;
- content mod: **no `exefs/subsdk9`**;
- runtime bootstrap: installed separately once.

---

## 6. REMAINING HIGH-PRIORITY VERSION COUPLING

Do **not** mass-convert every historical constant. Migrate live paths first and fail closed.

Priority order:
1. **P81 Ougi/Awakening policy parent** — still fingerprints/installs using v1.70-specific location logic.
2. **P89 actor predicate** — still sourced from `kP89ActorPred`.
3. **P125 cleanup request** — still contains a fixed cleanup instruction location; derive from the already-resolved UJ/session corridor.
4. **V2N StageRegistry lookup** — fixed today. The obvious signature duplicates in v1.70, so global unique scanning is unsafe. Resolve contextually from parent/caller/global relationship.
5. **Event236/stage helper calls** — replace remaining direct native helper/global constants with resolver accessors where live.
6. **Legacy diagnostics/probe offsets** — move out of the monolithic runtime bridge rather than blindly migrating all historical offsets.

Target end-state before changing bootstrap transport:
- live ModdingAPI/runtime path is resolver-/relationship-driven;
- expected v1.70 offsets are diagnostics only, never fallback execution addresses;
- content data remains independent of runtime bootstrap revision.

---

## 7. SOURCE VERIFICATION STATUS

Phase 1 source verification result before this checkpoint-discipline update:

`NSC_RUNTIME_R181_SOURCE_VERIFY=PASS`

Verified properties include:
- thin bootstrap/core split;
- preserved install order;
- stable C ABI;
- no packaged game `main`;
- bootstrap-only runtime artifact;
- generic ModPack CPK path with legacy fallback;
- R181 gate signature resolution;
- R172 CentralSetter resolver usage;
- exact original/P128 main hashes;
- exact 30-word reference delta;
- native gate, SetAnmDirect, D-pad selector/lookup, and StageRegistry v1.70 fingerprints.

R182 adds an additional source-verifier requirement that:
- `NSC2Switch_MASTER_CHECKPOINT_LATEST.md` is byte-identical to the current dated R182 FULL checkpoint;
- the mandatory checkpoint rule is present;
- the full R181 checkpoint remains embedded/preserved.

Hardware validation is still required before treating the modified runtime binary as a new gameplay baseline.

---

## 8. NEXT IMPLEMENTATION FRONTIER

Proceed with ModdingAPI Phase 2 in this order:
1. resolver/derived anchor for P81;
2. resolver/derived anchor for P89;
3. derive P125 cleanup from resolved UJ/session corridor;
4. replace remaining direct calls to already-known anchors/accessors;
5. contextual StageRegistry resolver;
6. split live runtime managers from legacy diagnostics/probes;
7. only after live paths are resolver-driven, evaluate replacing `subsdk9` transport with another loader while retaining `nsc_runtime_initialize()`.

Do not return to broad D-pad experimentation until architecture changes are source-verified and, where runtime behavior changes, hardware-tested.

---

# COMPLETE PREVIOUS MASTER CHECKPOINT — R181 AND ALL EARLIER HISTORY (PRESERVED)

# NSC2Switch MASTER CHECKPOINT — 2026-09-30 R181 FULL
## CURRENT RECOVERY OVERRIDE — FULL PRE-R178 D-PAD ELIGIBILITY ROLLBACK

> **Authoritative current section.** This block overrides R178-R180 eligibility conclusions wherever they conflict. Historical lineage is preserved below.

---

## R181 CURRENT FRONTIER

### Frozen invariants
- Game: NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS Switch v1.70.
- Title ID `0100FA10190A0000`.
- Build ID `48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39`.
- Original main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- Reference P128 main SHA256 `904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff`.
- Exact runtime main delta stays 30 words = condition5 + P67 1 + P128 24.
- R164 StageInfo hardware PASS/frozen.
- R172 UJ hardware PASS/frozen.
- Voice frozen/skipped.
- No char281-specific gameplay policy.

### R180 hardware result — FAIL as recovery, decisive diagnostically
- Compiled R180 artifact SHA256 `1c2dcb48512ce6715419729c60257ca6add6514cd88bcde13f94165f1904bdcd`.
- Left-only log24 SHA256 `3f26762c061e9c9c6479ea952b3130ae86c415821046bb3ca96c2a8dc59c6504`.
- User observation: Left still does not disappear / perform the intended transition.
- R180 READY proved the native gate at `main+0x59CEB4` was original Switch `E54 / #124` with zero gate writes.
- R180 nevertheless retained the Event236 opcode13 F30 writer; first opcode13 changed F30 `0->1`.
- Left selector remained correct `mode2 -> candidate921 -> actual921`.
- Route still reached `928 -> opcode23 SPTYPE_ACTION10 / PL_ANM930`, where non-UJ opcode23 remained `OP23_SAFE_SUPPRESS`.
- No opcode17 was executed.

### Critical comparison to the known pre-R178 hardware baseline
R175 Left hardware executed opcode13 and immediately continued into opcode12 without any F20/F30 mutation. Therefore R180 was only a gate rollback, not a true eligibility rollback.

### R181 exact A/B
1. Keep native Switch gate untouched at `main+0x59CEB4`:
   - `B94E5768` = `LDR W8,[X27,#0xE54]`
   - `7101F11F` = `CMP W8,#0x7C`
2. Restore Event236 opcode13 to shadow-only/read-only.
3. Opcode13 logs F30/F20 observations but writes neither field.
4. Keep non-UJ opcode23 suppressed for this A/B.
5. No action922 insertion, registry mutation, descriptor clone, action force, visibility/damage override, or char281 branch.
6. Preserve R172 UJ, P128, StageInfo, and voice state unchanged.

### R181 hardware test
- Fresh boot.
- Confirm `[NSC:R181] READY full_rollback=1 ... opcode13_shadow=1 writer13_mutation=0`.
- Press Left once only.
- Save full log and report whether Tobi again disappears/transitions toward the secret room.
- Do not mix Right into this boot.

### Decision
- **Left transition returns:** R178-R180 opcode13 mutation was the remaining regression cause; R181 becomes baseline and Right investigation resumes at candidate922 / non-UJ PL_ANM930.
- **Left still unchanged:** eligibility experiments are fully exonerated; compare pre-R178 lineage against R181 beyond opcode13 and focus on downstream action lifecycle. Do not revive F20/F30 writers.

### Source verification
`NSC_RUNTIME_R181_SOURCE_VERIFY=PASS`.

---

# HISTORICAL R180/R179/R178 AND EARLIER CHECKPOINT (PRESERVED)

# NSC2Switch MASTER CHECKPOINT — 2026-09-29 R179 FULL
## CURRENT RECOVERY OVERRIDE — R178 F20 MAPPING RETIRED; R179 F30 ELIGIBILITY CORRECTION

> **Authoritative current section.** This block overrides R178 conclusions wherever they conflict. The complete R178 full checkpoint and earlier lineage are preserved below so this remains standalone.

---

## R179 CURRENT FRONTIER

### Frozen invariants
- Game: NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS Switch v1.70.
- Title ID `0100FA10190A0000`.
- Build ID `48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39`.
- Original main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`.
- Reference P128 main SHA256 `904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff`.
- Exact runtime main delta remains 30 words = condition5 + P67 1 + P128 24.
- R164 StageInfo hardware PASS/frozen; keep `Tobi_Switch_R164_STAGEINFO_FIXED.zip`.
- R172 UJ hardware PASS/frozen.
- Voice remains frozen/skipped.
- Final architecture must remain generic, no char281 gameplay branch.

### R178 hardware inputs
- artifact `NSC-RUNTIME-R178-dpad-animation-eligibility-parity.zip` SHA256 `bc488257b35153b62c8c81a7bfd78dcb41a2b955d78c8b199c1dab6694754e01`.
- deployed original main hash exact; R178 subsdk9 SHA256 `ea47a5f14bf9b117d06b6d551dac1acf7dfaf16837b07234a2f7f69937fbc161`.
- Left log20 SHA256 `1a4098dd40ee3c6dd755ae2f50889f69a26e32ba935e75cbecfbf3b52e676ef6`.
- Right log21 SHA256 `a2a15dd423f0be0de69a9c9f6dcf3794f4ff3a88f50c9aa21c4bfedacb0bb940`.
- User result: Left no longer disappears/transitions as intended; Right still not invulnerable.

### R178 decisive runtime result
- R178 READY parity=1.
- Opcode13 writes F20 0->1 while F30 observed is 0.
- Left remains selector mode2 -> candidate921 -> actual921 -> 928 -> opcode23 SPTYPE_ACTION10.
- Right remains selector mode3 -> candidate922, lookup922 NULL -> native fallback921 -> 928 -> opcode23 SPTYPE_ACTION10.
- Both directions' non-UJ opcode23 remains V2H SAFE_SUPPRESS.
- Right log contains no opcode17 / DPAD17_APPLY, therefore Right charge100 is not armed and lack of invulnerability is expected.

### Critical correction from historical hardware
Pre-R178 hardware R175/R177 showed `f30=1` at the selector for both Left and Right. R178 changed the writer to F20 and produced `f30=0` plus the Left regression. Therefore the blanket PC->Switch -0x10 extrapolation is invalid for this D-pad-enable field.

**R178 F20 mapping is RETIRED.**

### R179 exact A/B
R179 restores exact PC field semantics:
1. Event236 opcode13 writes `actor+0xF30`.
2. Switch native gate at `main+0x59CEB4` changes:
   - original `LDR W8,[X27,#0xE54] ; CMP W8,#124`
   - R179 `LDR W8,[X27,#0xF30] ; CMP W8,#1`
   - words `B94F3368 7100051F`.
3. Non-UJ opcode23 remains suppressed.
4. No action922 insertion, registry mutation, descriptor clone, action force, visibility/damage override, or char281 branch.
5. R172 UJ, P128, stage, and voice state unchanged.

### R179 test
- Fresh boot Left once -> full log. Confirm R179 READY and DPAD_ENABLE f30->1. Observe whether intended Left disappearance/secret-room transition returns.
- Fresh boot Right once -> full log. Confirm selector mode/candidate and whether candidate922 availability changes. Test damage only if Right behavior changes.
- Do not add non-UJ SetAnmDirect or action922 repair until this exact eligibility correction is hardware-resolved.

### Source verification
`NSC_RUNTIME_R179_SOURCE_VERIFY=PASS`.

---

# HISTORICAL R178 FULL CHECKPOINT (PRESERVED VERBATIM)

# NSC2Switch MASTER CHECKPOINT — 2026-09-29 R178 FULL
## CURRENT RECOVERY OVERRIDE — R164 STAGE PASS, R172 UJ PASS, R178 D-PAD ANIMATION ELIGIBILITY PARITY

> **Authoritative current section.** This block overrides older conclusions below wherever they conflict. The complete historical checkpoint through R163 is preserved verbatim after this section so this remains a standalone recovery document.

---

## 0. GAME / BUILD IDENTITY — FROZEN

- Game: NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Title ID: `0100FA10190A0000`
- Build ID: `48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39`
- Original `main` SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- Reference P128 paired-main SHA256: `904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff`
- Runtime architecture: original on-disk main + resolver-driven `subsdk9` runtime patching.
- Frozen exact runtime main delta: **30 words** = condition 5 + P67 1 + P128 24.

Do not mix a patched historical main with a current runtime build. Current deployment main must remain the exact original hash above.

## 1. FROZEN FUNCTIONAL STATE

### R164 StageInfo — HARDWARE PASS / FROZEN
- Final StageInfo CPK packaging fix is hardware-PASS.
- `Tobi_Switch_R164_STAGEINFO_FIXED.zip` remains required baseline asset and must not be deleted as a superseded runtime source package.
- Stage workstream is frozen while D-pad is investigated.

### Voice
- Voice workstream is frozen/skipped by user for now.

### R172 UJ — HARDWARE PASS / FROZEN
- Tobi UJ no longer loops and works.
- PC opcode23 contract preserved for scoped UJ miss only:
  1. SetActionImmediate(param3)
  2. resolve PL_ANM
  3. SetAnmDirect(resolved index)
- R172 scope remains: Event236 opcode23, self/side0, custom semantic-UJ actor, generated OugiAwakening member, animation707 before/after SetActionImmediate, param3=8.
- Direct call is resolver-derived `main+0x766320(target,index,-1,0,1.0f)`.
- No char281 branch, no IXN0 guard, no force708/710.
- Non-UJ opcode23 remains safely suppressed in R178. **Do not change it in the R178 A/B.**

### P128
- Frozen. Do not reopen UJ admission/session hypotheses unless new evidence directly contradicts the hardware PASS.

## 2. ACTIVE TARGET — D-PAD LEFT / RIGHT ONLY

Intended Tobi v1.2 behavior:
- Right: activate Izanagi; about one minute of damage immunity / substitution recovery; UJ can dispel.
- Left: secret-room / left-Sharingan replacement transition; cancels/resets Izanagi.
- User explicitly reported Left also visually disappears first, so disappearance alone is not a valid universal failure criterion.

Historical opcode17 source parity remains valid:
- PC base `actor+0x12B88` -> Switch `actor+0x12B78`.
- arrow4 Right -> Switch `actor+0x12B84`.
- charge `100.0f` is valid; old <=16 clamp is retired.

## 3. R173–R177 D-PAD PROOF CHAIN

### R173
- Existing PlayAction hook reused; no new trampoline.
- Left/Right both eventually appeared as `921 -> 928 -> SPTYPE_ACTION10` when observed after native fallback.

### R174
Native selector table proven from Switch v1.70:
- mode0 -> 923
- mode1 -> 924
- mode2 -> 921
- mode3 -> 922

Native flow at `main+0x646CC8`:
- lookup candidate via `main+0x768E84(actor,candidate,1)`;
- if NULL, native `CSEL` substitutes PlayAction(921).

User A/B labels later fixed:
- Left = mode2 -> candidate921 -> actual921.
- Right = mode3 -> candidate922 -> native fallback actual921.

Retired: “Left/Right selector is the same.”

### R175 — actor lookup matrix
Left log16:
- candidate921 exists.
Right log17:
- candidate922 returns NULL for both flag=1 and flag=0.
- `native_candidate_missing=1`.

### R176 — global vs actor-local registry
Right log18 proves:
- global index922 exists and names `PL_ANM_SPTYPE_ACTION02` / `SPTYPE_ACTION02`;
- actor-local lookup922 is NULL;
- 921 and 923..930 are actor-present;
- native remap is identity (922->922).

### R177 — upstream action-record matrix
Tested compiled R177 artifact:
- ZIP SHA256: `55584dc2c70d70dd629140e5072ccb12e924a2bf115483dc58a902a0e97d3955`
- deployed original main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- `subsdk9` SHA256: `011193375462e0c3d7462168d7a2a7e56b2b3ce318a303de01bd17a185bc2728`
- `uzuy_log(19).txt` SHA256: `f80c0aee28868edcd27b232b141c2ca9a7d50ff023a801d0e641b66f10951e6f`

Right log19 proves record922 is an empty/default record upstream of actor binding:
- binding = 0
- r1 = 0
- r2 = 0
- descriptor = module/static default (`0x1a297a8720` in that run)
- adjacent normal action records have r2=1; idx927 demonstrates r1=0 alone is not sufficient to make a record invalid.
- R177 itself is read-only: `registration_change=0`, `descriptor_clone=0`, `action_force=0`, `state_changed=0`.

## 4. CRITICAL R177 ASSET FORENSICS — ACTION02 CLONE THEORY RETIRED

Active R164 Switch CPK string census:
- has `PL_ANM_SPTYPE_ACTION01`;
- has ACTION03..ACTION10;
- does **not** contain `PL_ANM_SPTYPE_ACTION02` as a per-character resource.

Historical Library source recovered:
- `P4_TOBI_DECRYPT_COMPILE_STAGE.zip`
- original input `Tobi (Madara Uchiha) (1).unse` SHA256 `8287a62466e9cbad0efc40129b9421d0ab90639b4ca7928b5103abbeaf7782a0`

The historical PC-source/decrypted staging shows the same resource pattern: ACTION01 and ACTION03..10, no per-character ACTION02.

Therefore:
- alpha14b exporter did **not** drop ACTION02;
- per-actor action922 absence is source-consistent;
- **do not clone/insert action922**;
- **do not force PlayAction(922)**;
- R176/R177 findings remain useful diagnostics, but “missing 922 binding is the final root bug” is retired.

## 5. PC ULTIMATESTORMAPI SOURCE ROOT — D-PAD ANIMATION ELIGIBILITY PATCH

Recovered UltimateStormAPI source audit (`HookFunctions.cpp`) contains an explicit `//Dpad animations` native compatibility patch executed before the MovesetPlus function hook.

For PC SC1.70 semantics it rewrites the hard-coded native eligibility test:

```text
[actor + 0xE64] == 124
```

to:

```text
[actor + 0xF30] == 1
```

PC patch bytes for the displacement/immediate fields:
- original: `64 0E 00 00 7C`
- replacement: `30 0F 00 00 01`

This means PC UltimateStormAPI makes D-pad animation eligibility **data-driven via an enable flag**, instead of remaining hard-coded to Kaguya/char124.

## 6. CRITICAL SWITCH LAYOUT CORRECTION — OPCODE13 F30 WAS WRONG

Two independent PC->Switch actor layout translations are proven:
- CharID: PC `+0xE64` -> Switch `+0xE54`
- D-pad charge: PC `+0x12B88` -> Switch `+0x12B78`

Both are exactly `-0x10`.

Therefore the PC D-pad enable flag `+0xF30` maps to Switch **`+0xF20`**.

This corrects the previous Switch opcode13 implementation that wrote `actor+0xF30`.

Static Switch evidence also proves `+0xF30` already has independent native meaning:
- `main+0x7A7594`: write zero to actor+F30
- `main+0x7A788C`: write one to actor+F30
- `main+0x7A78AC`: write zero to actor+F30
- `main+0x7E74A4`: read actor+F30

Thus the historical observation “F30 was already 1 before D-pad activation” does **not** mean Izanagi had already activated. The old F30-activation-success interpretation remains retired.

## 7. R178 — D-PAD ANIMATION ELIGIBILITY PARITY

Source package:
`NSC2Switch_RUNTIME_R178_DPAD_ANIMATION_ELIGIBILITY_PARITY_FULL_SOURCE_DROPIN.zip`

SHA256:
`330561e579d10ce8cb445f109e3ce32ea0cf1bcd60e9f3efc647cfc033ab1310`

Source verifier:
`NSC_RUNTIME_R178_SOURCE_VERIFY=PASS`

### 7.1 Exact R178 functional delta

**A. Event236 opcode13 writer**

Old Switch implementation:
```text
actor+0xF30 = p2
```

R178:
```text
actor+0xF20 = p2
```

Marker:
```text
[NSC:R178] DPAD_ENABLE actor=... side=... char=... p2=... f20=before->after f30_observed=...
```

**B. Separate native D-pad eligibility patch**

This patch is separate from and does not alter the frozen 30-word V2D/P128 plan.

Switch original at `main+0x59CEB4`:
```text
B94E5768  LDR W8,[X27,#0xE54]
7101F11F  CMP W8,#0x7C
```

R178:
```text
B94F2368  LDR W8,[X27,#0xF20]
7100051F  CMP W8,#1
```

The surrounding Switch function obtains an actor in X27 and turns the char124 equality into a boolean used to update a UI/control-state object, making this the strongest Switch semantic homolog of the PC `DPadHudAddress` / `//Dpad animations` patch.

R178 install is fail-closed:
- validates both original words before any write;
- writes only the two words above;
- verifies both words after write;
- no hook/trampoline is added.

### 7.2 R178 safety constraints
- exact P128/V2D 30-word plan unchanged;
- R172 UJ unchanged;
- R175/R176/R177 read-only diagnostics retained;
- selector table unchanged;
- native fallback unchanged;
- non-UJ opcode23 unchanged/suppressed;
- no action922 force;
- no registry insertion;
- no descriptor cloning;
- no char281 gameplay branch;
- no StageInfo mutation;
- no voice mutation;
- zero extra trampoline.

Boot success marker:
```text
[NSC:R178] READY parity=1 dpad_enable_off=0xf20 ... hud_gate_off=0x59ceb4 ...
```

## 8. R178 HARDWARE TEST — NEXT EXACT STEP

Run **two separate fresh boots**:

A. Left once only, save log.
B. Right once only, save log.

Required evidence:
- `[NSC:R178] READY parity=1`
- `[NSC:R178] DPAD_ENABLE`
- R175 selector PRE/POST
- R176/R177 matrices
- downstream Event236 / PlayAction route
- visual/gameplay outcome

Interpretation:
- If Right changes materially under eligibility parity, the missing PC native gate was causal; only then evaluate whether non-UJ opcode23 also needs source-parity SetAnmDirect behavior.
- If Right route remains identical and no opcode13/enable marker is reached before selector/fallback, investigate the control-side writer/order that should set the flag; do not clone action922.
- If Left regresses, inspect the same flag lifecycle; do not globally force visibility or damage immunity.

## 9. CURRENT RETIRED D-PAD HYPOTHESES

Do not revive without new contradictory evidence:
- F30 is Izanagi activation-success state;
- abs(charge)<=16 is required;
- Left and Right are decoded as the same selector;
- candidate table is wrong;
- remap922 is wrong;
- `PL_ANM_SPTYPE_ACTION02` was dropped by alpha14b exporter;
- actor action922 should be cloned from 921/923;
- force PlayAction922 is the next fix;
- global visibility/no-damage workaround.

## 10. ACTIVE NEXT FRONTIER

**R178 hardware A/B only.**
Do not change opcode23 in the same build; preserve causal isolation.

---

# COMPLETE HISTORICAL LINEAGE THROUGH R163

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


---

# R163 — V2P HARDWARE PASS + FINAL CPK TOC ROOT CAUSE

Date: 2026-09-28

## Hardware / artifact result
V2P is stable and passive. Custom CPK bind succeeds before the native StageInfo requests. V2P hardware log proves:
- Tobi_Switch.cpk bind success at 7.359046s.
- native data/stage/StageInfo.bin.xfbin request at 10.078413s with cpk_bound=1.
- native AdvStageInfo request immediately after, also with cpk_bound=1.
- therefore StageInfo-before-CPK ordering hypothesis is RETIRED.
- V2N later reports STG_2TOB_UNI_LT key 0x01D1CA7E found=0.
- vanilla STAGE_SI45A key 0x2BCB5498 found=1 on the same registry chain.
- no Unmapped InvalidateNCE flood in the V2P run.

## Final CPK forensic audit
User supplied the exact mounted Tobi_Switch.cpk.
SHA256: e61bdb5faf60be186828769a1d064c98f0682ed02f39c6b9929eaab8e7ef69b7
Size: 174006320 bytes.
CRI CPK TOC: 93 files.

The final package contains ZERO stage registration files:
- data/stage/StageInfo.bin.xfbin ABSENT.
- data/stage/AdvStageInfo.bin.xfbin ABSENT.
- data/stage/stageFilter.xfbin ABSENT.
- stage_config.ini ABSENT.
- Stages/STG_2TOB_UNI_LT/... ABSENT.

The ASCII STG_2TOB_UNI_LT appears three times, all inside data/spc/mtobprm.bin.xfbin as event/content references; this is not stage registry metadata.

## Root cause boundary — PROVEN
The authored .unse contained Stages/STG_2TOB_UNI_LT/data/stage/StageInfo.bin.xfbin and historical compiler analysis observed a temporary/static 181->182 merge. The final CPK omits that merged StageInfo from its TOC.

Therefore the active defect is:
**compiler/staging/packaging drops the merged global StageInfo before final CPK emission.**

Retired hypotheses:
- wrong Event236 CRC;
- wrong numeric stage ID;
- invalid V2N registry chain;
- CPK bind failure;
- CPK binds after StageInfo initialization;
- runtime StageInfo reindex required;
- manual PostStage required.

## Next action
Patch/rebuild the CPK compiler pipeline so the final Tobi_Switch.cpk TOC contains:
`data/stage/StageInfo.bin.xfbin`
with the merged custom STG_2TOB_UNI_LT record (historically expected 182 records).

Static gate before hardware:
1. final CPK TOC has global StageInfo path;
2. extracted global StageInfo contains STG_2TOB_UNI_LT;
3. merged record count / structure validates;
4. Tobi SPC/audio/UI payload remains intact.

Then test with the current safe V2P/V2N runtime. Expected decisive marker:
`[NSC:V2N] STAGE_REGISTRY ... text=STG_2TOB_UNI_LT ... found=1`

V2O direct `main+0x835FAC` runtime reload remains permanently retired.


# R180 ADDENDUM — D-PAD NATIVE GATE ROLLBACK RECOVERY
Date: 2026-09-30

## New hardware evidence
- log22 = Left-only R179. User: no change vs R178; Left does not perform the expected disappearance transition.
- log23 = Right-only R179. User: no change vs R178; Right is not invulnerable.
- R179 runtime is correctly deployed and F30 writer executes.

## Exact log conclusions
- Left selector remains mode2/base_candidate921 and candidate921 resolves normally.
- Right selector remains mode3/base_candidate922; actor lookup922 remains NULL and native fallback plays921.
- Both runs later reach action928 -> Event236 opcode23 p3=77 / SPTYPE_ACTION10 -> PL_ANM930.
- Both runs use V2H OP23_SAFE_SUPPRESS; call_766320=0.
- Both logs contain zero opcode17. Therefore Right=100 is never armed in R179.

## R178/R179 eligibility gate hypothesis retired
R179 restored the opcode13 writer from R178 F20 back to F30, but gameplay did not recover. The remaining common gameplay delta is the PC-style rewrite of Switch main+0x59CEB4. That gate rewrite is therefore retired. Do not carry it into future builds unless new evidence uniquely revalidates it.

## R180 exact delta
- Event236 opcode13 remains actor+0xF30.
- main+0x59CEB4 is left untouched and only fingerprinted:
  - 0xB94E5768 = LDR W8,[X27,#0xE54]
  - 0x7101F11F = CMP W8,#0x7C
- gate_patch_words=0.
- exact30 runtime patch unchanged.
- R172 UJ unchanged.
- R175/R176/R177 diagnostics unchanged.
- non-UJ opcode23 suppression unchanged.
- action922 registry unchanged.
- no action force, descriptor clone, visibility override, damage override, or char281 gameplay branch.

## R180 test
Primary A/B: fresh boot -> Left once -> save full log. PASS for recovery if expected disappearance/secret-room transition returns.
Only after saving: optional separate fresh boot -> Right once for regression comparison. Right is not expected to become invulnerable in R180 because opcode23 remains suppressed and opcode17 cannot execute.

If Left recovers, next frontier is no longer eligibility/F20/F30. Resume from the two proven downstream gaps: Right candidate922 missing actor binding and non-UJ opcode23/PL_ANM930 execution semantics. Do not re-open UJ/P128/stage/voice.
