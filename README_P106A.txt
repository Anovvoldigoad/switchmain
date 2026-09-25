NSC2Switch P106A — +0x520 ENTRY PROOF (ONE-TRAMPOLINE SWAP)

Purpose
- Do NOT revisit state125/261/74. Those are proven downstream cleanup symptoms.
- Answer the one remaining question: does custom Tobi action708 ever enter native
  +0x520 controller main+0x7E64D4, the controller that contains PlayAction710?

Design
- Parent: P96 (therefore P50 victim-safe + P89 admission preserved).
- Exactly one new whole-function trampoline: main+0x7E64D4 (+0x520).
- P105B +0x4C0 hook is retired; main+0x7DDD94 is native again.
- Read-only. No force708/710, no actor/state/mode writes, no char281 gameplay branch.
- Logs ENTER/EXIT as CTRL520 + STATE520 with shared seq/phase.

Static anchors
- +0x520 entry: 0x7E64D4
- only direct BL into +0x520: 0x488B28
- native action710 construction: 0x7E6EA8 MOV W1,#710
- native PlayAction call: 0x7E6EC4, runtime return/caller 0x7E6EC8

Single-session test
1. Vanilla char91: successful UJ/cinematic.
2. Custom Tobi: reproduce 700->707->708 failure.
3. Send full log + compiled artifact.

Decision
- Custom action708 has NO CTRL520 row: root is upstream dispatch/eligibility before 0x488B28.
- Custom enters CTRL520 but no 710: trace first internal +0x520 branch differing from vanilla.
- Custom enters CTRL520 and 710 appears: validate cinematic and move to post-710 completion only.
