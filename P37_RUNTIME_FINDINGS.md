# P37 live Uzuy outcome — actor visibility remains unresolved

## Ground truth (user report, 24 October 2026)

- **P37 boots and reaches battle.**
- **The opponent is still invisible as in earlier Tobi versions.**
- User supplied a new `uzuy_log.txt` (1765 lines) for this exact test.
- No evidence that the restored three shared-global files change the missing-opponent symptom.
- The failing P36 packaging regression (81 new CRILAYLA, 93 CC2 entries) did not recur in P37; P37 retained 90 stored entries byte-for-byte, the carrier's `Sorted=0` and `Align=512`.

## Actual log facts

- [6.235 s] P32 CPK_BIND `sim:data/moddingapi/Tobi_Switch.cpk`, priority 32, **result=1, bind_id=3**.
- [8.941 s] `CHAR id=281` resolves to `mtob`.
- [9.577–171.976 s] 50 P34 `PROCESS_BEGIN` / `FILE_OPEN` / `PROCESS_END` sequences. All **50 P34 FILE_OPEN result=1**; all 50 `PROCESS_END status=1 readerr=0`. These indicate loader/file read completion but not successful actor creation or render.
- In 48 P32 `LOAD_STATUS` lines, none returns status 5 in the recorded window. `mtobbod1acc` returns a nonnull named chunk (e.g. at 49.993, 70.430, 103.085, 115.948, 171.312 s).
- [81.450–82.379 s] **28** `HW.Memory <Error> Unmapped Device ReadBlock` messages, at contiguous 0xC241C000–0xC2480000 addresses. The emulator reports missing `uniformAndStorageBuffer16BitAccess` and `uniformAndStorageBuffer8BitAccess` Vulkan features at setup; it continues despite warnings.
- [173 s] shutdown/reinitialization includes additional frontend and host-memory assertions; these are not demonstrated to cause opponent disappearance.

## Critical trace-scope caveat from actual checked-in native source

`overlay/source/program/nsc_cpk_bridge.cpp` defines:
```cpp
bool IsInterestingPath(const char* path) {
    if (!path || !*path) return false;
    if (PathContainsTrackedCustom(path)) return true;
    return BoundedContains(path, "mtob", 512, 8);
}
```

P32/P34 logs are generated only when `IsInterestingPath(path)` is true, hence
`conditionprm`, `damageprm`, and `privateCamera` will **never** appear
in these trace logs unless their paths contain a tracked custom code (they do not).
Their absence in the current log **does not show that the runtime did not load them**.
Consequently, successful P37 boot with unchanged symptoms cannot distinguish
(a) the restored shared globals not being resolved from this CPK,
(b) globals being used but not relevant to opponent visibility, or
(c) their effect being overshadowed by another actor/render issue.

## Next engineering decision

1. **Stop speculative CPK packaging/global parameter changes.** P37 is a controlled negative result for the three-global replacement.
2. Prioritize tracing the native **actor creation, model/material registration, render visibility, and scene effect/layer setup** when `mtob` is selected, and whether the invisible opponent has valid actor identity/transform; current `nuccFileLoad` read/ready status only covers a different stage.
3. Compare against an actually **playable older legacy main+subsdk9** version if its binaries/patches are accessible. That is the best-known functional reference; identify changes required to preserve actor rendering instead of repeatedly changing CPK assets.
4. Where tracing globals, explicitly expand the native trace filter to `conditionprm`, `damageprm`, and `privateCamera` and log source/binder provenance, **not merely request status**, before claiming priority or no-op. Do not deploy an invasive unverified native hook.
5. Treat the 28 unmapped device reads as a correlated signal to compare against an unmodded control on the same emulator/driver; they **are not evidence enough** to blame the GPU driver. No driver changes are recommended from this log alone.

**Current status:** P37 boots; disappearing opponent NOT FIXED; render/actor cause NOT IDENTIFIED; updated-resistant hook-free RomFS mounting is still unproven.
