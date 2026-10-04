# R204O Boot-Safe READ_STAGE Subcall Trace

Read-only continuation of R204O/R204M preview tracing for Switch v1.70.

R204M hardware proved generic `bod1` and `bod1acc` pass FILE_OPEN and READ_DISPATCH but enter READ_STAGE without exiting. R204O keeps every prior probe and adds direct substage hooks for:

- `main+0x118819C` STREAM_ATTACH
- `main+0x11882AC` STREAM_READ
- `main+0x120A99C` READ_HEADER
- `main+0x120AA5C` READ_PAYLOAD
- `main+0x120B35C` READ_FINAL

Deep internal logs are restricted to generic `data/spc/bod1*`, known-good `5mdrcharsel`, and `mtobprm_load` so earlier traffic cannot exhaust the log budget. No path, state, return value, CPK binding, gameplay logic, or character ID is changed.


## Boot-safe change
R204N failed before READY because exlaunch aborted in `AllocForTrampoline`. R204O installs only 9 focused trampolines needed to map the body read and split READ_STAGE; all unrelated owner/status/chunk hooks are omitted in this diagnostic build.
