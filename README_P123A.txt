NSC2Switch P123A — Compact Conditional Outer Corridor Bridge (R139)
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
exlaunch pin: 229bbd6

WHY P123A
P122 boots and P120 still proves raw15->10, but custom UJ still takes natural 707->708 with no cinematic/710. P122 globally bypassed both C48 reject branches and changed nothing, so C48 alone is not the final blocker. Exact static flow shows two more exits before outer setup main+0x7EF098: type9 result at 0x77C4B4 and helper result at 0x77C520.

P123A ARCHITECTURE
- Paired main is restored to the normal paired baseline SHA256 1adc4dfe...34de0. P121B/P122 global C48 NOPs are gone.
- Compact install parent: P81 functional chain + direct P89 bridge. Historical P82/P84/P85/P88B read-only hook layers are NOT installed, freeing trampoline capacity.
- Five P123 inline callsite bridges only:
  1) 0x77C474 event raw load: first appended custom semantic-UJ event can overlay W8 to10 and arm actor.
  2) 0x77C490 actor/victim C48: native called once; 0->1 only in armed custom semantic707 corridor.
  3) 0x77C4A4 peer/attacker C48: same narrow overlay.
  4) 0x77C4B0 type9 query: native called once; nonzero->0 only in same corridor so native CBZ takes the successful control route.
  5) 0x77C51C helper 0x7F78FC: native called once; non-null->null only in same corridor so native CBZ reaches the outer setup path.
- No direct call to 0x7EF098. Native main+0x77C5E8 remains responsible for reaching it.
- No action/session/state/event cursor/damage table/game actor field writes.
- No force708/710 and no char281 branch.

EXPECTED RUNTIME MARKERS
[NSC:P123A] READY ...
[NSC:P123A] GATE ... bridge=1 ... raw=15 out=10
[NSC:P123A] ACTOR_C48 ...
[NSC:P123A] PEER_C48 ...
[NSC:P123A] TYPE9 ...
[NSC:P123A] LOOKUP ...

INTERPRETATION
- If GATE->ACTOR_C48->PEER_C48->TYPE9->LOOKUP all appear and action710/cinematic starts, downstream admission is causally restored; use the native values to identify exactly which gate(s) need the final upstream semantic repair.
- If a marker in that ordered chain is missing, the first missing marker is the exact runtime frontier.
- If all five appear but no 710/cinematic follows, outer setup main+0x7EF098 is now reached by construction through its native callsite; next investigation is inside 0x7EF098/session lifecycle, not B9E4/raw damage/C48/708.

BUILD
python3 verify_p123a_source.py
git add -A
git commit -m "P123A compact conditional outer corridor bridge"
git push
Download GitHub Actions artifact: NSC-P123A-compact-conditional-outer-corridor
Deploy BOTH paired main and subsdk9 from the artifact, then fresh boot.
