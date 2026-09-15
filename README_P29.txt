NSC2Switch P29 — nuccFileLoad prm_load trace
===========================================
TARGET: Switch v1.70 / Program ID 0100FA10190A0000
DIAGNOSTIC ONLY. No character/resource remap is performed.

Why P29 exists
--------------
P27 proved ID281 + PSP527+ + custom characterSelect/playerSetting can preview/VS/battle when characode 281 is temporarily 1nrt.
P28 produced Nanashi preview with a 9nns alias, but native disassembly shows duplicate vanilla path/cache semantics make that test non-conclusive for CPK timing.

Static v1.70 proof used by P29
------------------------------
main+0x876104 builds: data/spcload/<characode>prm_load.bin.xfbin
main+0x1161B40 registers the path and creates the file-load object through 0x116175C.
0x116175C calls main+0x1206B4C (nuccFileLoadList find-or-create).
main+0x1206B4C calls 0x1206C9C only when a fresh object is required.
main+0x1207EFC returns the load status for a path; it returns 4 itself when the path is absent from the file-load list.
main+0x11617CC treats status 2 as loaded and emits an error when status 5 is observed.

P29 hooks (read-only except existing proven CPK mount)
------------------------------------------------------
0x473190   existing external CPK bind bridge
0x3F4150   characode getter; discovers custom char codes generically
0x1206B4C  LOAD_REQ path/result
0x1206C9C  LOAD_CREATE path/result
0x1207EFC  LOAD_STATUS path/status

All new trace hooks are fingerprint guarded. Logs are filtered to custom prm_load paths and capped.
No char ID/resource alias is applied.

Build
-----
The user's Android/Termux environment previously reported DEVKITPRO/DEVKITA64/toolchain missing.
Use the included GitHub Actions workflow. Put this kit in a GitHub repository, then run:
Actions -> Build NSC P29 nuccFileLoad trace -> Run workflow.
Download artifact: NSC-P29-nuccFileLoad-trace-subsdk9

Deploy
------
Start from CLEAN P23A (the icon-PASS mtob baseline), NOT P27/P28/P26.
Replace only:
  atmosphere/contents/0100FA10190A0000/exefs/subsdk9
with the P29-built subsdk9.
Keep P23A main, Tobi_Switch.cpk, and loose charicon_s.gfx unchanged.
Do not keep P24/P25 loose-resource diagnostics.

Test
----
1. Boot.
2. Enter character select.
3. Hover Tobi once.
4. Try select -> map -> VS only if stable.
5. Close emulator and send full fresh Uzuy log.

Search for:
  [NSC:P29] READY
  [NSC:P29] CPK_BIND
  [NSC:P29] CHAR id=281 ... code=mtob
  [NSC:P29] LOAD_REQ ... mtobprm_load...
  [NSC:P29] LOAD_CREATE ... mtobprm_load...
  [NSC:P29] LOAD_STATUS ... mtobprm_load... status=N

Run locally on the log if desired:
  python3 analyze_p29_log.py uzuy_log.txt

Status interpretation
---------------------
- no LOAD_REQ for mtobprm_load: registration/request path is not reaching nuccFileLoadList as expected.
- LOAD_REQ + LOAD_CREATE: fresh mtob prm_load object creation is attempted.
- status=4: 0x1207EFC cannot find the path in nuccFileLoadList at query time.
- status=5: native nuccFileLoad error state. main+0x11617CC logs this as a failed xfbin load.
- status=2: native IsLoaded passes; move downstream into prm_load parsing and individual row resource loads.

Important
---------
P29 is generic in the executable path. It learns custom code strings from IDs above vanilla max 280.
The literal mtob check exists only as a diagnostic fallback to avoid missing the first fixture event due to hook/log ordering.
Final architecture must remove fixture-specific behavior.

P29B CI FIX (2026-09-16)
-------------------------
The GitHub Actions workflow intentionally does NOT run dkp-pacman.
The official devkitpro/devkita64 Docker image already contains the Switch toolchain,
switch-dev/libnx and related build dependencies. Running pacman from CI can fail at
repository sync (for example HTTP 403 from pkg.devkitpro.org) and is unnecessary.
