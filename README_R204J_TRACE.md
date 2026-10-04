# R204J native charsel registry-process trace

R204J keeps every R204I hook read-only and adds the exact post-registration boundary for the target `mtobcharsel.xfbin`.

New probes:
- `OWNER_TREE_VERIFY`: after `main+0x1161B88` returns, re-finds the inserted hash node in the native registry tree and reports the stored owner/path, the nested `OWNER_INIT5` owner, and whether they are the same object.
- `REGISTRY_PROCESS` at `main+0x1161C98`: reports whether the exact registry containing mtob is actually traversed after registration and whether the target node remains present.
- `TARGET_REGISTRY_OWNER_READY`: while that exact registry is being traversed, logs every owner readiness check regardless of path, so a prior blocking owner cannot be hidden by the normal path filter.

No arguments, returns, paths, hashes, load states, registry nodes, or gameplay state are modified. R215A `sound.cpk` remains unchanged.

Hardware protocol: cold boot, hover one working vanilla preview briefly, then target slot for 10+ seconds, exit, and provide full log plus visual result.

## R204J build-only logger fix (R220)
The original R204J READY banner exceeded exlaunch LoggerMgr's 512-byte snprintf buffer and failed under `-Werror=format-truncation`. R220 splits the same diagnostic metadata across `READY`, `READY_FLAGS`, and `READY_HOOKS`. Hook offsets, fingerprints, callbacks, return values, and runtime behavior are unchanged.
