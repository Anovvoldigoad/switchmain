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


# R177 delta — D-pad action descriptor matrix

R176 hardware proved the decisive registry split for Right D-pad candidate 922:
- global index922 exists as `PL_ANM_SPTYPE_ACTION02`;
- actor-local lookup922 is null for both flag=1 and flag=0;
- native remap is identity 922->922;
- all neighbouring SPTYPE entries 921 and 923..930 are globally present and actor-bound.

R177 is read-only. At the existing PlayAction fallback callsite it inspects the already-proven native action-record path:
`actor+0xE90 -> actor+0x11660[e90] -> table_obj -> table_base -> record[index*0x18]`.
For indexes 921..930 it logs the actor state-table binding, record pointer, descriptor pointer, record qwords, descriptor fields +0x6C/+0x72, and the descriptor key at +0x94.

No actor table writes, descriptor cloning, action forcing, new hook, or new trampoline are added.
