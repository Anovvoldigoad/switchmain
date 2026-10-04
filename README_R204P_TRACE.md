# R204P Boot-Safe READ_STAGE Preamble State Trace

Read-only continuation of R204O for Switch v1.70.

R204O hardware proved `bod1` and `bod1acc` enter `main+0x120A860` READ_STAGE but do not reach any of the traced deeper substages (`STREAM_ATTACH`, `STREAM_READ`, `READ_HEADER`, `READ_PAYLOAD`, `READ_FINAL`). Therefore R204P removes those unreachable substage trampolines and snapshots the READ_STAGE context immediately before native execution.

Installed trampolines: 4 only:
- PROCESS `main+0x116F404`
- FILE_OPEN `main+0x1170FB0`
- READ_DISPATCH `main+0x11705F0`
- READ_STAGE `main+0x120A860`

New read-only logs:
- `PREAMBLE_CTX`: qwords at `read_context+0x1B0..0x1E0`; `+0x1C8` is explicitly important because the native READ_STAGE prologue loads X1 from `[X0,#0x1C8]`.
- `PREAMBLE_LOCAL`: local reader vtable and virtual methods at vtable+0x28 and +0x50, plus the raw `+0x1C8` field rendered as a pointer.

Decision rule: compare known-good `5mdrcharsel` versus generic `bod1/bod1acc`. A null or structurally divergent `+0x1C8`/neighbor field before the NCE storm moves the blocker to READ_STAGE preamble metadata initialization, upstream of XFBIN parsing.

No path rewrite, CPK bind, return override, gameplay patch, state mutation, or character-ID patch is performed.
