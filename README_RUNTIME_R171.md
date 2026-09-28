# NSC2Switch Runtime R171 — UJ707 Flag70 Native Release

R170 hardware proof isolated the UJ-miss stall to `anim+0x70 bit0`: the native gate at `main+0x769A4C` returned 0 with `reason=anim_flag70` while action707 remained active.

R171 is a functional root candidate. It does **not** force action708, 710, 77, or 74. On the exact terminal custom-UJ whiff signature only (`707`, semantic+membership, side0, E80=1, E94/E98=8/8, E9C=0, BDA4=1, busy1264=0, native animation timing already complete), it clears only bit0 of `anim+0x70`, preserving all other bits, then calls the original native gate exactly once.

Expected success path: `[NSC:R171] ... match=1 ret=1 flags70=0001->0000`, followed by native `PlayAction708`, then the existing native cleanup chain.

CPK R164 stays frozen. Voice remains frozen.
