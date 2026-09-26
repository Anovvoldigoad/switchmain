P126A — single actor-C48 reject bypass probe (R142)

Runtime proof from P125:
- custom Tobi semantic UJ reaches P124 GATE bridge=1 raw15->10
- it never reaches AFTER_ACTOR
- P125 cleanup is session=0 mature=0 and remains125
- Naruto UJ is safe

P126 paired-main delta:
- main+0x77C494 native CBZ W0,0x77C5EC -> NOP
- main+0x77C490 actor C48 BLR remains native
- peer C48 + reject remain native
- type9, lookup, 0x7EF098 remain native
- P125 session-qualified fallback remains intact

Purpose:
Open only the first proven reject and expose the next native frontier via existing P124/P125 markers.
No char281 branch. No direct 7EF098. No force708/710. Zero new hooks/trampolines.

Test:
1) Naruto UJ once
2) Tobi victim UJ once
3) Tobi own UJ once
4) save log before recovery
