NSC2Switch P81A — OugiAwakening Policy Bridge
===============================================

Target:
Naruto x Boruto Ultimate Ninja STORM CONNECTIONS
Nintendo Switch update 1.70

Purpose
-------

P80B proved the failing actor's native virtual +0x1288 decision becomes
positive because SW_MTOB_XH / condition index512 satisfies native
wanted_type=1.

P81A ports the data-driven OugiAwakening compatibility policy onto the
exact Switch Ultimate-Jutsu decision invocation.

Generated membership:
overlay/source/program/p81_ougi_awake_ids.hpp

Current audited payload SHA256:
4322e4ab30547321abc6cd24322a5ba98f8e7d0ddafa853039234c397ccfe6cb

Current fixture membership:
281

No char281 gameplay branch exists.

Exact Switch target
-------------------

Policy function:
main+0x7EAC34

Exact UJ caller:
0x7F4588 BLR X8

Return LR:
main+0x7F458C

Policy
------

native_ret = Orig(actor)

Only for exact UJ caller:

if semantic UJ is active
and actor ID belongs to generated OugiAwakening membership
and native_ret != 0:

    policy_ret = 0

Otherwise native_ret is preserved.

P81A does NOT:
- modify SW_MTOB_XH
- modify descriptor field +0x0C
- force state87
- force action700
- rewrite action445
- map selector1 to selector8
- override F58
- special-case char281

Expected success
----------------

[NSC:P81A] POLICY ... member=1 semantic=1 native=1 policy=0 allow=1

then native engine:

[NSC:P77A] UJ_ACCEPT ... ret=1
requested=700
PlayAction700
