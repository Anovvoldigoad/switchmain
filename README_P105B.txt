NSC2Switch P105B — boot-safe single-trampoline sibling-controller proof (compile-safe logging revision)

WHY P105B EXISTS
P105A did not boot because exlaunch exhausted its trampoline JIT pool while installing the second new whole-function hook. The boot log explicitly reported AllocForTrampoline failure before P105A READY.

P105B CHANGES
- parent: P96
- exactly ONE new trampoline: main+0x7DDD94 (+0x4C0 controller)
- +0x520 controller main+0x7E64D4 remains native/unhooked
- vanilla +0x520 is identified using the existing P50/P59 PlayAction caller main+0x7E6EC8
- read-only; no force708/710 and no char281 branch

COMPILE-SAFE LOGGING REVISION
The first P105B source revision had a 539-byte READY format string, exceeding LoggerMgr's 512-byte snprintf buffer and failing under -Werror=format-truncation before linking. This revision shortens READY and splits controller logging into paired CTRL4C0 + STATE4C0 lines sharing the same seq/phase. Gameplay/hook logic is unchanged. verify_p105b_source.py now enforces a conservative <512-byte bound for every P105B log format.

TEST
Boot once and verify [NSC:P105B] READY ... probe=1.
Then in the same session run a successful vanilla char91 UJ followed by failing custom Tobi UJ.
Send the full log plus the built artifact.

BUILD
python3 verify_p105b_source.py
git add -A
git commit -m "P105B compile-safe logging"
git push

Expected workflow: Build NSC P105B single-trampoline sibling-controller proof
Expected artifact: NSC-P105B-single-trampoline-sibling-controller-proof
