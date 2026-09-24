NSC2Switch P96A — Action Descriptor Transition Trace
====================================================

Purpose
-------
P95A proved the observed semantic-custom action707->708 transition reaches
main+0x772594 from parent return main+0x7EFF8C. The same stack provenance also
contains main+0x7EFF40, which is the return after main+0x7EFF3C BL 0x3F5540.
Static v1.70 analysis resolves that branch as a non-empty inline descriptor key
at descriptor+0x94 being translated by the native string->action-id resolver.

P96A is the final read-only discriminator before a gameplay compatibility write.
It compares the native action-707 descriptor used by vanilla successful UJ and
semantic custom UJ.

What P96A logs
--------------
Marker: [NSC:P96A] ACTDESC

- actor+0x218 current state pointer and current action at +0x2C
- actor+0xE70 action-family mode
- actor+0xE90 action-table selector
- action-table cache slot: actor+0x11660 + e90*8
- table object / table base
- raw 24-byte records for action index 707
- descriptor fields +0x6C / +0x72
- inline transition key at descriptor+0x94
- candidate descriptor keys for 707 / 791 / 833 / 875
  (native main+0x769B04 e70 modes 0/1/2/3)

Static chain proved before P96A
-------------------------------
main+0x766A98  current action via actor+0x218/+0x2C
main+0x769B04  700..908 mapping; e70 1/2/3 => +84/+126/+168
main+0x7948E8  action-table cache at actor+0x11660 + e90*8
main+0x782C08  record = table_base + mapped_index*0x18
main+0x7EFEBC  transition controller
main+0x7EFF3C  descriptor+0x94 string lookup path
main+0x3F5540  forwards descriptor key to global action-name map
main+0x80EFEC  string lookup returning numeric action ID
main+0x7EFF88  vtable+0xEB0 virtual dispatch
main+0x772594  generic action wrapper

Safety
------
- zero new hooks
- zero new trampolines
- read-only
- no action/state writes
- no force708 / force710
- no char281 gameplay branch
- P95 0x1000 stack scan is muted in P96A because parent identity is already proven
  and the emulator logged unmapped stack-page invalidations at the old scan edge.

Test
----
One session is enough:
1. vanilla UJ that reaches cinematic/action710
2. custom semantic UJ reproducer that goes 707->708
3. send full uzuy log

Fast analysis
-------------
python3 analyze_p96a_log.py uzuy_log.txt

Expected decisive comparison
----------------------------
Compare VANILLA_710 key707/descriptor with CUSTOM_708 key707/descriptor.

If custom key707 is non-empty and vanilla key707 is empty/different while both
use cur_action=707, e70=0, e90=0, then the early 708 is directly data/descriptor-
driven. The next build can implement the narrow generic semantic-UJ compatibility
bridge at the proven transition boundary.

If descriptors/table selection are unexpectedly wrong before the key lookup,
fix table selection instead of suppressing 708.
