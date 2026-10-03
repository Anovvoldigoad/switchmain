# R204B — Native `mtob` Loader/Chunk Trace

Temporary diagnostic runtime for the R203A native-ID46 `1nrt -> mtob` carrier.

## What it does
Installs only read-only hooks at the already-audited v1.70 boundaries: LOAD_REQ, LOAD_CREATE, LOAD_STATUS, FILE_OPEN, PROCESS, and CHUNK. Paths/keys containing `mtob` are traced even though the current control uses native CharacodeID 46.

## What it deliberately does NOT do
- no external CPK bind
- no game `main` replacement
- no ID281/range expansion
- no path rewrite or alias
- no forced load status
- no return-value modification
- no gameplay/UJ/D-pad patch

## Build
Upload this source tree to GitHub and run the included workflow. Artifact: `NSC2Switch-R204B-NATIVE-MTOB-TRACE`.

## Deploy
Keep the exact R203A RomFS carrier that produced the empty Naruto preview. Add only the compiled `atmosphere/contents/0100FA10190A0000/exefs/subsdk9` from the R204B artifact. Do not deploy any other NSC2Switch ExeFS override or external ModdingAPI CPK.

Cold boot, enter character select, hover the native Naruto slot once, then close the game/emulator and preserve the full log.

Expected marker: `[NSC:R204B] READY installed=1 ...`

Analyze: `python3 analyze_r204b_log.py uzuy_log.txt`

The decisive outputs are the first `LOAD_STATUS ... status=4/5`, first `FILE_OPEN ... result=0`, or first `CHUNK ... result=0/null`.
