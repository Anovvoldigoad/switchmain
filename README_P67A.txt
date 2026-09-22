NSC P67A — ACTIVE SELECTOR1 CONSUMER BRIDGE

P66 RESULT
P66 inline-hooked BLR X8 at 0x7F46B4 and caused a
vanilla UJ regression. That architecture is removed.

STATIC PROOF
Active input function contains:

0x7F4728 MOV X0,X19
0x7F472C BL  0x7ABE9C
0x7F4730 CBNZ W0,...

Inside 0x7ABE9C:

0x7ABF2C MOV W1,#1
0x7ABF30 BL  0x7C6280

Thus the helper is a direct native selector1 consumer.

P67 CHANGE
Existing semantic selector1 overlay is enabled at exact
active-player return address 0x7F4730 in addition to the
previous proven router callers.

Native result is always preserved.

NO:
- char281 branch
- F58 forcing
- action700 forcing
- state87 forcing
- selector8 mapping
- P66 inline BLR replacement
