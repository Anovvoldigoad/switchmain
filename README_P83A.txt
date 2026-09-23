NSC2Switch P83A — Slot +0x1928 Ougi Policy Bridge
==================================================

Target:
Naruto x Boruto Ultimate Ninja STORM CONNECTIONS
Nintendo Switch update 1.70

P82 runtime
-----------

P81 successfully clears the earlier +0x1288 awakened/type1 veto.

Observed downstream sequence:

P81 allow=1
P77 ret=1
0x794EC8 ret=0
action445

The deeper P82 post-gate/control-getter probes were not reached.

P83 target
----------

Custom actor vtable +0x1928 resolves statically to:

main+0x7D34E0

Exact UJ-corridor caller:

0x7F4744  LDR X8,[X8,#0x1928]
0x7F4748  BLR X8
0x7F474C  CBZ W0

Policy
------

Native function is always called first.

Only exact caller return 0x7F474C may be adjusted.

native 0 -> policy 1 only when:

- actor identity is valid
- semantic Ultimate Jutsu is active
- actor ID belongs to generated OugiAwakening membership

Otherwise native result is preserved.

P83 does not:
- special-case char281
- force state87
- force action700
- rewrite action445
- hook the inline BLR
- modify condition records
- override generic control getters

Expected runtime
----------------

[NSC:P83A] SLOT1928_POLICY
member=1
semantic=1
native=0
policy=1
allow=1

Then P82 downstream tracing should reveal the next native corridor.
