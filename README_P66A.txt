NSC P66A — VIRTUAL UJ SEMANTIC BRIDGE

CORE CHANGE

P65 hooked concrete F58 implementation 0x7D3138.

Static disassembly proves the real player-UJ consumer is polymorphic:

7F46A4 LDR X8,[X19]
7F46A8 MOV X0,X19
7F46AC MOV W1,WZR
7F46B0 LDR X8,[X8,#0xF58]
7F46B4 BLR X8
7F46B8 CBZ W0,7F4738

P66 hooks 0x7F46B4.

The inline callback:
1. obtains original actor-specific function pointer from X8;
2. calls it with the original X0/W1/W2 arguments;
3. queries the existing selector1 semantic for the same actor;
4. writes W0 = native || semantic;
5. leaves the native CBZ at 0x7F46B8 untouched.

Paired main retains:
0x7F2A9C BD001FE0 -> D503201F

FORBIDDEN / ABSENT
- no char281 branch
- no force action700
- no force state0x87
- no selector8
- no 445->700
- no raw Event236 restoration
- no old 0x7E1404 Ougi tail
