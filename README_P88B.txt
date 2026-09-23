P88B BOOT-SAFE UJ HELPER PROBE
P88A artifact/package hashes are valid, but P88A failed boot after installing eight global/shared trampolines. P88B returns to proven P87A instrumentation and adds ONLY whole-function 0x8B30E4.
Apply from proven P87A source:
 python3 APPLY_P88B_BOOTSAFE_UJ_HELPER.py
 python3 verify_p88b_source.py
 git diff --check
 git add -A && git commit -m "P88B boot-safe UJ helper probe" && git push
First test BOOT ONLY. Confirm [NSC:P87A] READY and [NSC:P88B] READY. Then matrix: vanilla XA x2, vanilla UJ x2, custom XA x2, custom intended XXA/UJ x2.
