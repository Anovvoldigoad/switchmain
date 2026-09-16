NSC2Switch P30 — prm_load CHILD TRACE
=====================================

Parent evidence
---------------
P29 clean P23A run proved:
  CHAR id=281 -> mtob
  LOAD_CREATE data/spcload/mtobprm_load.bin.xfbin -> non-null
  LOAD_REQ    data/spcload/mtobprm_load.bin.xfbin -> same non-null object
  LOAD_STATUS data/spcload/mtobprm_load.bin.xfbin -> status=2

Therefore the parent mtob manifest is loaded. P30 moves exactly one level downstream.

What P30 traces
---------------
1) Existing P29 characode + CPK bind hooks.
2) nuccFileLoadList LOAD_REQ / LOAD_CREATE / LOAD_STATUS for ANY path containing a
   discovered custom characode (P29 only traced prm_load paths).
3) main+0x3EAE70 ccGetChunkBinary(full_path, key) -> result pointer.
   P30 logs only calls whose path or key contains a discovered custom characode.

P30 is read-only. It does not alias IDs, substitute paths, alter return values, or
change resource data.

Fixture fallback
----------------
"mtob" is used only as an ordering fallback before ID281 has been observed. Generic
tracking remains ID>280 -> discovered characode, supporting future custom characters.

Deploy
------
Start from the exact P29 CLEAN P23A READY-TO-DEPLOY package that produced the valid
P29 status=2 result. Replace ONLY:
  atmosphere/contents/0100FA10190A0000/exefs/subsdk9
with the P30-built artifact.

Do NOT change main, Tobi_Switch.cpk, charicon_s.gfx, PlayerSetting, or characterSelect.

Test
----
Fresh boot -> character select -> hover Tobi -> select Tobi -> choose map -> let the
failed transition reproduce -> stop emulation -> send the complete fresh Uzuy log.

Expected markers
----------------
[NSC:P30] READY ... chunk=0x3eae70
[NSC:P30] CHAR id=281 ... code=mtob
[NSC:P30] LOAD_* path=...mtob...
[NSC:P30] CHUNK path=...mtob... key=... result=...

Interpretation
--------------
- First CHUNK with result=0/null: exact file/key boundary is identified.
- Custom LOAD_STATUS=4: child path is absent from nuccFileLoadList.
- Custom LOAD_STATUS=5: child path reached loader but load failed.
- Custom LOAD_STATUS=2 + CHUNK null: file loaded but requested chunk/key is absent.
- All custom CHUNK results non-null: move downstream to prm_load row consumer / actor
  construction rather than adding assets blindly.

Current static audit note
-------------------------
The 60-row manifest contains 36 mtob row references (33 unique custom names). The
existing checkpoint audit found 32/33 staged custom paths; mtobskl3 is the only absent
custom path. That makes it a high-value suspect, NOT a proven root cause. P30 is meant
to prove which row/path/key actually fails before any data patch is attempted.
