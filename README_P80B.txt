NSC2Switch P80B — Deep Condition Trace
=======================================

Target:
Naruto x Boruto Ultimate Ninja STORM CONNECTIONS
Nintendo Switch update 1.70

Purpose
-------

P79A proved that the failing semantic-enabled actor follows:

Predicate A = 0
Predicate B = 1

immediately before ordinary requested action445.

P80B traces the native condition classifier used by Predicate B.

Predicate B:
main+0x7EACF0

Condition query:
main+0x777388

Exact Predicate-B query caller:
main+0x7EAD04

Exact return LR:
main+0x7EAD08

Condition descriptor getter:
main+0x754A80

Actor condition collection:
actor+0x10F80


Runtime markers
---------------

[NSC:P80B] READY
[NSC:P80B] QUERY
[NSC:P80B] DUMP_BEGIN
[NSC:P80B] CAND
[NSC:P80B] DUMP_END


Deep trace fields
-----------------

QUERY:
actor
collection
wanted_type
native result
matched_index
E94
E9C

CAND:
ordinal
node
entry
condition index
descriptor pointer
name pointer
after index
descriptor +0x0C
descriptor +0x10
descriptor +0x14
descriptor +0x18
wanted type
type_match
native_return


Safety
------

Read-only diagnostics.

Native returns are preserved.

No char281 gameplay branch.
No forced state87.
No forced action700.
No selector1->selector8 mapping.
No F58 override.
No forced condition-query result.


Runtime procedure
-----------------

Use the custom actor as player.

Wait for stable battle state.

Attempt XXA once.

Continue logging for approximately 2-3 seconds after ordinary action445.

Preserve the FULL emulator log.

Large logs are acceptable.
