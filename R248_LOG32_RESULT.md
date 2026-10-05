# R248 hardware result — uzuy_log(32).txt

Locked result:
- R248 installs read-only successfully.
- Target Create input: `entryCC=1`.
- Descriptor lookup succeeds and returns `d4=46`.
- Target model enters init with `model+0x38 = 46`.
- `main+0x3F4130(46)` returns non-null (`0x3aba4772d0` in this run).
- Nevertheless model init returns with `model+0x90 = NULL`.
- Create readiness remains `result=0` repeatedly.

Therefore:
- `IDENTITY_46_TABLE_LOOKUP_MISSING = FALSIFIED`.
- The old unaudited internal-ID hypothesis is not the active blocker on the native-ID46 control path.
- Current blocker is after successful identity lookup and before the successful `model+0x90` producer store.
- Static recovery narrows the next gates to file resource lookup at `0x6EACF8 -> 0x1207B38`, chunk lookup at `0x6EAD50 -> 0x120A3D4`, then allocator `0x6EAD6C -> 0x116AE60`.
