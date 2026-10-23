# P35 — Runtime trace cross-check: 2026-10-21 Uzuy log

Source: user-supplied `uzuy_log.txt` (1,534 log lines) from the earlier
Tobi Switch 1.70 test session. This note contains aggregated facts and
selected path observations, not a copy of the user's raw log.

## Exact captured counters

| Event | Observations |
| --- | ---: |
| P34 PROCESS_BEGIN | 46 |
| P34 FILE_OPEN | 46 (all `result=1`) |
| P34 PROCESS_END | 46 (all `status=1 readerr=0`) |
| P32 LOAD_REQ | 58 |
| P32 LOAD_CREATE | 47 |
| P32 LOAD_STATUS | 47 (43 `status=2`, four `status=0`) |
| P32 LOAD_STATUS `status=5` | 0 |
| P32 CHUNK | 1 (non-null) |
| Uzuy `HW.Memory Unmapped Device ReadBlock` | 13 |

Scope correlation matters: PROCESS_END status=1 is **not** proof of
final completion. Separate LOAD_STATUS observations show status=2.
P34 path logging included `sim:` and `ROM:` provider prefixes;
do not join these blindly by string to unprefixed LOAD_STATUS paths.

## Specific path transitions

`data/spcload/mtobprm_load.bin.xfbin`: LOAD_STATUS=2 at 10.357447s.

`data/spc/mtobbod1acc.bin.xfbin`:
- 66.876245s LOAD_STATUS=0
- 66.908160s LOAD_STATUS=2
- 67.808451s LOAD_STATUS=0
- 67.845427s LOAD_STATUS=2
- 74.284504s LOAD_STATUS=0
- 74.442489s LOAD_STATUS=2

`data/spc/mtobbod1_col3.xfbin`:
- 66.908212s LOAD_STATUS=0
- 66.941228s LOAD_STATUS=2

`CHUNK path=data/spc/mtobbod1acc.bin.xfbin key=mtobbod1acc`
returned a non-null pointer at 75.230540s.

The 13 `Unmapped Device ReadBlock` errors occur from
108.091502s to 108.370566s. They do not establish whether a resource
lifetime bug, asset compatibility issue, or emulator rendering behavior
caused the invisible opponent. A timestamp comparison alone is insufficient.

## Disposition

This capture does NOT reproduce the historical P31/P32 open-failure/status=5
branch. It supports moving investigation to resource lifecycle and
actor/render registration, while retaining independent evidence of the
data-source/binder and content collision state.

The user's gameplay report (opponent temporarily visible during particular
Tobi attacks, but not ultimate jutsu) is a separate observation; it is not
a trace-backed causal diagnosis. The 46 successful FILE_OPEN results are
for captured attempts only, not every game resource.

No game binaries, mod resources, or emulator settings are changed by P35.
