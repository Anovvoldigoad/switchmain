NSC2Switch P79A — Dual Subpredicate Runtime Probe
=================================================

Target:
Naruto x Boruto Ultimate Ninja STORM CONNECTIONS
Nintendo Switch update 1.70

Purpose
-------

P78 proved that the semantic-enabled failing custom actor takes the
ALT route and does not reach the active UJ helper.

Static analysis resolved the upstream virtual +0x1288 implementation
to main+0x7EAC34.

P79A splits that composite predicate into its two direct components:

Predicate A
-----------
Target:
main+0x7EAC70

Exact parent return LR:
main+0x7EAC40

Runtime marker:
[NSC:P79A] PRED_A


Predicate B
-----------
Target:
main+0x7EACF0

Exact parent return LR:
main+0x7EAC60

Runtime marker:
[NSC:P79A] PRED_B


Safety
------

P79A is read-only.

It preserves every native return value.

It does NOT:
- force state 0x87
- force action700
- force UJ acceptance
- map selector1 to selector8
- override F58
- special-case char281
- inline-hook the virtual BLR


Runtime test
------------

Use the custom actor as player.

Wait until battle is stable.

Attempt XXA once.

Stop logging 2-3 seconds after action445.

Interpretation:

PRED_A ret=1, no B:
  +0x1288 positive result originates in Predicate A.

PRED_A ret=0 followed by PRED_B ret=1:
  +0x1288 positive result originates in Predicate B /
  actor+0x10F80 collection query.
