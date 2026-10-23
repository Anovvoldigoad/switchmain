# P34 — thread-scoped native XFBIN load trace

P33 passed its 5/5 unit tests but correlates P32 `FILE_OPEN` and `PROCESS` using path order alone.
P34 adds **read-only native observations** so PROCESS and FILE_OPEN can be scoped per Switch
thread. It does not patch file results, replace resources, or modify Tobi gameplay.

- `PROCESS_BEGIN tid=N attempt=M path=...` immediately before native `Orig`
- `FILE_OPEN tid=N path=... request=... slot=... result=...` after native `Orig`
- `PROCESS_END tid=N attempt=M path=... status=... readerr=...` after native `Orig`

The call at main+0x116F47C enters FILE_OPEN (main+0x1170FB0) from inside the
PROCESS routine at main+0x116F404, making on-thread scope containment
suitable for observing this branch. Thread ID is collected using libnx
`svcGetThreadId(&tid, CUR_THREAD_HANDLE)`; 0 indicates failure and MUST
NOT be paired by the parser. P32 log messages are preserved.

Build the normal exlaunch subsdk9 via existing workflow `build-subsdk9-p32.yml`.
Deploy **only** after GitHub Actions compile success. This is not a playable mod.

Analyzer: `python3 analyze_p34_log.py fresh_uzuy_log.txt --json`
Unit tests: `python3 -m unittest -v test_analyze_p34.py`

Nine tests cover open failure, XFBIN read failure, retry recovery,
concurrent threads, nesting, invalid thread ID, incomplete scope,
mismatch, and a nested different-path open.

**Limitations:** logger quotas (512 PROCESS / 512 FILE_OPEN) can truncate
observations; an XFBIN may still fail in other branches. Zero or missing
thread IDs and orphan events are not classified. Native hooks must be tested
in emulator/console before claiming their logs are correct. No runtime
success is implied by CI compile success.
