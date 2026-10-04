# R204S Target-Only Stream Forensic Trace

R204S fixes a diagnostic blind spot discovered from the R204O/R204R hardware logs. R204O deep-stage counters were consumed by high-volume `mtobprm_load` traffic before the later generic body requests arrived, so absence of body `STREAM_*` markers was a false negative.

R204S keeps the proven boot-safe 9-trampoline layout but the deep filter is restricted to:
- `5mdrcharsel.xfbin` as known-good control
- `data/spc/bod1*` as the target family

`mtobprm_load` is deliberately excluded.

The `STREAM_READ_ENTER` record is expanded to report:
- stream position
- stream buffer pointer
- buffered-byte count
- reader pointer and vtable
- reader vtable+0x28 method and module offset
- wait/sync object
- stream state
- destination pointer and requested read size

Purpose: identify whether the first generic-body read enters with a null/invalid buffer or destination, an abnormal size, or stalls inside the native reader method. No path, return value, state, gameplay logic, ID, or CPK binding is modified.

Keep R223A `sound.cpk` byte-identical and keep `main` clean. Replace only `subsdk9`.
