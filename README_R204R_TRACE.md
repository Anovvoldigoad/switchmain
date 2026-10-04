# R204R — One-Shot READ_STAGE Root-Cause Probe

R204R replaces the serial one-hypothesis-per-build workflow with callsite breadcrumbs inside native `main+0x120A860` (READ_STAGE). It keeps the five proven trampoline hooks (PROCESS, FILE_OPEN, READ_DISPATCH, READ_STAGE, CTX_ACCESS) and adds nine inline post-call breadcrumbs that faithfully reproduce the single native instruction they replace.

One hardware run can identify the first native boundary that does not return:
- POST_ACCESSOR1
- POST_TLS1 (accessor #2 + TLS push returned)
- POST_STREAM_ATTACH
- POST_READ_HEADER
- POST_HELPER_116B880
- POST_HELPER_116AF60
- POST_HELPER_12099C8
- POST_READ_PAYLOAD
- POST_READ_FINAL

Read-only invariants: no main replacement, no gameplay patch, no path rewrite, no return override, no ID patch, no CPK bind. Keep R223A sound.cpk exact and main IPS clean.
