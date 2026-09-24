P97A — EARLY TRANSITION GUARD / FIRST FUNCTIONAL HANDOFF FIX CANDIDATE

Purpose
- Preserve the proven P89 semantic-UJ admission architecture.
- Add exactly one whole-function trampoline at main+0x7EFEBC.
- Defer descriptor-key-driven transitions only while a data-driven semantic-UJ member remains in the proven action707 pre-handoff state.
- Return native no-transition value 0; do not force action710 and do not rewrite action708.

Runtime proof behind this build
- P95: failing 707->708 parent is main+0x7EFF8C.
- P96: vanilla successful 707 has empty descriptor+0x94 key; semantic custom 707 has non-empty key PL_ANM_SPSKILL_1_LOOP and maps 707->708 before native handoff.
- Static main+0x7EFEBC resolves descriptor+0x94 then calls vtable+0xEB0; returning 0 is the native no-transition result.

Guard criteria (all required)
- semantic selector1 latch active
- actor is a data-driven ougiAwakening member
- current action == 707
- e70 == 0 and descriptor707 has a non-empty key
- E94 == 136, E9C == 0
- BDA4 == 1, BDA8 == 0, BDC8 == 0

Expected custom result
- [NSC:P97A] GUARD ... guard=1 during early 707 maturation
- no PlayAction708 from caller 0x7725D0
- actor remains in 707 long enough to reach native PlayAction710 from 0x7E6EC8

Test order
1. Boot/menu/battle sanity.
2. Vanilla UJ: must still reach 710/cinematic.
3. Custom semantic UJ: check GUARD=1 and whether it reaches 710/cinematic.
4. If own UJ passes, test custom as victim of vanilla UJ to ensure P50/Event236 victim safety remains intact.
5. Test one ordinary custom jutsu/normal action transition as regression control.

If boot fails before READY, classify as trampoline-capacity failure, not semantic failure. P90A previously proved two extra whole-function trampolines can exhaust the pool; P97 adds exactly one.

P97A v2 compile-order hotfix
----------------------------
The first P97A source kit placed InstallP97Internal() before the shared
MatchWords()/LogFingerprintFail() definitions without forward declarations.
GCC therefore failed before link. v2 adds declarations only; guard semantics,
hook offset 0x7EFEBC, fingerprints, actor gates and return policy are unchanged.
