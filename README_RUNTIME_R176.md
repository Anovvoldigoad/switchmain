# NSC2Switch R176 — D-pad Action Registry Matrix Trace

R176 is a read-only diagnostic build.

Hardware R175 established:
- LEFT: mode2 -> candidate921 -> available -> actual921.
- RIGHT: mode3 -> candidate922 -> actor lookup NULL -> native fallback actual921.
- 922 is NULL with both flag=1 and flag=0.

R176 reuses the existing PlayAction hook and compares:
- global entries 921..930 (main+0x3F5560),
- actor-local entries 921..930 flag=1/0 (main+0x768E84),
- remap results 921..924 (main+0x769B04).

Look for:
[NSC:R176] ACTION_REGISTRY
[NSC:R176] ACTION_REGISTRY_SUMMARY

No action force, registry insertion, descriptor clone, new trampoline, P128 change,
R172 UJ change, StageInfo change, voice change, or non-UJ opcode23 behavior change.

Test:
1. fresh boot
2. press RIGHT once
3. save full log
A LEFT run is optional; RIGHT is decisive because candidate922 is the failing path.
