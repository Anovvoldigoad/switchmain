NSC2Switch P99A — CLEANUP GATE +0x1278 TRACE (Switch v1.70)

Purpose
=======
P98B proved the custom action708 path explicitly requests state125 from
caller main+0x7EB28C. Static v1.70 resolution shows the chain is:

  cleanup corridor main+0x7EAF90
    -> actor vslot +0x1988
    -> custom runtime impl main+0x7EB270
    -> native state-request wrapper
    -> state request 125
    -> E9C 0->125
    -> state125
    -> PlayAction261

P99A moves one gate upstream. It hooks the custom runtime implementation of
actor vslot +0x1278 at main+0x7EB518. This predicate is executed before the
cleanup corridor can call +0x1988.

P99A is diagnostic only. It does NOT block state125, does NOT alter action708,
does NOT force action710, and does NOT write E94/E9C/EA4/BDA4/BDA8.

What it logs
============
[NSC:P99A] TOPO
- dynamic vtable +0x1278/+0x12C8/+0x12D0/+0x1988 targets at PlayAction707/708/710

[NSC:P99A] GATE1278
- native predicate return value
- caller offset
- actor vtable and dynamic +0x1278 / +0x1008 targets
- action/E94/E98/E9C/EA4/EA8/BDA4/BDA8/BDC8
- E70/E74/E7C
- actor+F24
- actor+0x106F4
- actor+0x10F54 / +0x10F58 / +0x10F60 / +0x10F64

Recommended runtime test
========================
In one boot/session:
1. Perform one VANILLA Ultimate Jutsu that successfully reaches cinematic/710.
2. Perform Tobi/custom Ultimate Jutsu reproducer through 707->708 and failure.
3. Upload the log and compiled artifact.

We compare GATE1278 ret/raw dependencies between successful vanilla and custom.
The fixture ID is for diagnosis only; P99A contains no char281 gameplay branch.

Architecture
============
Functional parent: P96A observation chain (thus P89 bridge + P50 victim-safe
behavior remain inherited). P97 and P98 are NOT installed by P99A.
P99A adds one read-only whole-function trampoline at main+0x7EB518.
