P85A — F58 INTENT/INPUT PROBE (READ ONLY)
==========================================

Parent: R84 / P84A.
Purpose: identify the exact native XA-vs-XXA discriminator before any new gameplay override.

New static proof used by P85A:
- custom actor vtable +0xF58 resolves to main+0x7D3138;
- active classifier calls +0xF58 at main+0x7F46B4, return LR main+0x7F46B8;
- historical vanilla runtime at that exact caller:
    ordinary XA -> F58 ret=0, E94=1
    native UJ   -> F58 ret=1, E94=1 -> requested700 / PlayAction700
- therefore F58 is a real native intent/eligibility boundary.
- P85A DOES NOT override F58. Orig() return is preserved exactly.

Why not reuse P83 policy:
P83 replaced the complete +0x1928 return. Static disassembly now shows +0x1928 contains several internal gates (including H750170, E94==0x3F, vtable/state/condition tests). Overriding its whole return is too broad and explains ordinary XA -> UJ regression.

Why H750170 is not enough:
Static disassembly shows main+0x750170 is a global linked-list predicate with many callsites and no actor parameter. It is useful context, not yet a UJ-input identity.

APPLY
-----
cd /storage/emulated/0/Downloads
python APPLY_P85A_F58_INTENT_PROBE.py
python verify_p85a_source.py
git diff --check
git status --short

Stage ONLY intended source files (never git add .):
git add overlay/source/program/main.cpp \
        overlay/source/program/nsc_cpk_bridge.cpp \
        overlay/source/program/nsc_cpk_bridge.hpp
git commit -m "P85A read-only F58 intent probe"
git push

BUILD
-----
Use the current GitHub Actions build path. P85 is source-only/read-only; active paired main must remain the known source-parity main.
Expected startup markers include the inherited P84/P81/P50 chain plus:
[NSC:P85A] READY ... f58_probe=1 ... readonly=1 preserve_orig=1

HARDWARE TEST ORDER
-------------------
Tobi starts already awakened. Do NOT press awakening first.

Do four controlled groups from neutral state:
1. vanilla character: ordinary XA x2
2. same vanilla character: native UJ x2
3. Tobi/custom: ordinary XA x2
4. Tobi/custom: intended XXA/UJ x2

Let the log be large. Do not trim it.
Also run victim safety once after the input tests: Tobi as victim of vanilla enemy UJ must remain visible/playable.

The log should contain P85 triplets:
[NSC:P85A] F58 ...
[NSC:P85A] INPUT ...
[NSC:P85A] MAP ...

ANALYZE
-------
python analyze_p85a_log.py /path/to/uzuy_log.txt > P85_ANALYSIS.txt

DECISION RULE
-------------
- If a raw input bit/signature separates vanilla UJ + Tobi XXA from both XA classes, use it as the intent discriminator candidate.
- If Tobi XXA has a distinct UJ-like input signature but native F58 remains 0, back-slice the first F58 internal gate that rejects it and bridge ONLY that semantic policy, data-driven by OugiAwakening membership.
- If Tobi XA and XXA are already identical at F58 input state, move upstream into the input-router producer; do NOT force F58 or +0x1928.

FORBIDDEN
---------
No char281 gameplay branch; no force F58; no force state87/action700; no selector8 mapping; no raw Event236 restore; no inline BLR replacement; no +0x1928 global override.
