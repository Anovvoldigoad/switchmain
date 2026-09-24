NSC2Switch P93A — maximum useful zero-extra trace

Drop-in semantics:
1. Extract this ZIP into the repo root.
2. git add -A
3. git commit -m "P93A maximum useful zero-extra trace"
4. git push
5. Download GitHub Actions artifact: NSC-P93A-maximum-useful-zero-extra-trace

P93A adds NO new trampoline. It reuses already-proven hooks and only adds read-only
state snapshots around PlayAction, central setter, action-mode base, P81 policy,
P77 UJ accept, P88B helper, P89 actor predicate, and Event236.

Important correction from P92A: actor+E6C and actor+E70 are already known in this
source as skill1/skill2 slots. Their vanilla/custom difference is therefore expected
loadout data and must NOT be treated as a root-cause state or forced to vanilla values.
