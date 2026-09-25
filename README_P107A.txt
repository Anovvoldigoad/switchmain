NSC2Switch P107A — EXACT POST-708 STATE BRIDGE (FUNCTIONAL CANDIDATE)

Why this is not another cleanup hold
- P101 already held state125 and did NOT create action710.
- P102 held action74 and only restored movement.
- P106A proved custom char281 never enters +0x520 at all, while vanilla state137
  enters +0x520 mode0 from the same generic dispatcher 0x7A8350 and produces 710.

Proven native chain
- custom action708 cleanup producer: 0x7EB27C MOV W1,#125
- virtual call: 0x7EB288, preserved return/caller: 0x7EB28C
- state request implementation: 0x7A89A4, W1=requested state
- state request natively validates and stores requested state to actor+E9C
- generic dispatcher reads active E94 and calls its controller at 0x7A8350
- state137 selects +0x520 in successful vanilla; +0x520 produces PlayAction710 at 0x7E6EC4

P107A policy
- Exactly one new whole-function trampoline at 0x7A89A4 (same budget as P106A).
- P106 +0x520 probe is retired; +0x520 is native again.
- Map request125 -> request137 ONLY when all are true:
  side0, semantic UJ, generated ougiAwakening member, exact caller 0x7EB28C,
  arg2=1, arg3=0, current action708, E94=63, E98=136, E9C=0, BDA4=1, BDA8=0, BDC8=0.
- Calls Orig(actor, mapped_state, arg2, arg3) exactly once.
- No direct E9C/E94/action/control write. No force708/710. No char281 branch.

Test
1. Boot and verify [NSC:P107A] READY ... candidate=1.
2. Tobi: perform one Kamui UJ.
3. Desired proof: one [NSC:P107A] BRIDGE req=125 mapped=137 ret=1,
   then native PlayAction710 from caller 0x7E6EC8 and cinematic.
4. If own UJ succeeds, immediately regression-test Tobi as victim of enemy UJ.
