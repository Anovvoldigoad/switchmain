# R75 / P66A

P65A established that hooking concrete implementation 0x7D3138 is
insufficient.

P66A uses the statically proven callsite:

actor -> vtable -> +0xF58 -> BLR X8 @ 0x7F46B4

The original actor-specific function is called first.

Return policy:

native true -> true
native false + selector1 false -> false
native false + selector1 true -> true

No character-specific executable branch.
