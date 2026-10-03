# R204H Native Charsel Owner/Poll Trace

Read-only diagnostic runtime derived from R204G. R215A sound.cpk remains unchanged.

New probes:
- `main+0x11616E8` OWNER_INIT: generic load-object initialized for a path; logs owner/path/mode/load pointer.
- `main+0x11617CC` OWNER_READY: readiness poll; logs owner/path/load/result.
- `main+0x1161858` OWNER_STATE: status-class query; logs owner/path/load/state.

R204H also traces every path containing `charsel.xfbin`, in addition to mtob/1nrt/2tob. No path rewrite, return override, CPK bind, gameplay patch, or ID patch is installed.

Hardware protocol: keep R215A sound.cpk. Cold boot. Hover one known-working vanilla character for a few seconds, then the target slot for 10+ seconds, then exit and save the full log. Compare OWNER_INIT/OWNER_READY/OWNER_STATE between native and mtob charsel.
