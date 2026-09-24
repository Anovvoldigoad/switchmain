NSC2Switch P103A — SpecialCond factory selector bridge

Purpose
=======
Port the exact UltimateStormAPI SpecialCondParam::Create_NSC semantic to Switch:

    original(remap(characterSelector), context)

Current generated mapping
=========================
276 -> 276  (COND_9ISH)
281 -> 58   (COND_2DNZ)

Switch proof
============
- PC and Switch special-condition selector tables match 82/82 in selector order.
- Switch dispatcher: main+0x7CAB00.
- direct callsite main+0x722F2C supplies W0 selector and W1 context.
- selector58 is present and resolves to factory main+0x7CC8E0.
- selector281 is absent and otherwise falls back to default factory0.

P103A behavior
==============
- one new trampoline at main+0x7CAB00;
- map only the dispatcher selector argument from generated data;
- preserve context argument;
- call original exactly once;
- preserve actor identity and all actor fields;
- no action/state/control writes;
- no force708/710;
- P102 HOLD74 is retired/absent;
- P96/P89/P50 baseline remains active.

Expected log markers
====================
[NSC:P103A] READY ... probe=1
[NSC:P103A] REMAP ... selector=281 mapped=58 ...

Test
====
Perform one Tobi Kamui UJ. Confirm whether 700 -> 707 -> 708 now reaches 710/cinematic.
Also smoke-test victim UJ restore and normal movement.
