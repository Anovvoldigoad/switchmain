# R204M Full Preview Pipeline Trace

Read-only diagnostic runtime for NSC Switch v1.70. R204M retains every R204L owner/file/resource probe and widens the post-open path so a single hardware run can identify the exact blocking boundary.

Additional R204M markers:
- `PROCESS_ENTER` / `PROCESS_EXIT` around `main+0x116F404`.
- `READ_DISPATCH_ENTER` / `READ_DISPATCH_EXIT` at `main+0x11705F0`, including provider vtable method target.
- `READ_STAGE_ENTER` / `READ_STAGE_EXIT` at `main+0x120A860`.
- `REQUEST_FINALIZE_ENTER` / `REQUEST_FINALIZE_EXIT` at `main+0x1171080`.
- `READ_CLEANUP_ENTER` / `READ_CLEANUP_EXIT` at `main+0x1170550`.

No CPK bind, path rewrite, return override, numeric-ID patch, gameplay patch, or state mutation is installed. Keep the R223A sound.cpk unchanged for the controlled test.
