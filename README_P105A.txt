P105A — DUAL SIBLING-CONTROLLER ENTRY/EXIT PROOF (READ ONLY)

Target
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID 0100FA10190A0000
- main Build ID 48ece454b61412b9fb46fab2be3f5ef7b2804f39
- exlaunch pin 229bbd6

Why P105A
P104B runtime produced no GATE samples, while the same session directly proved:
- vanilla char91: action707 -> PlayAction710, caller return main+0x7E6EC8; static producer main+0x7E6EC4 inside controller main+0x7E64D4 (+0x520).
- custom char281: action707 -> 708, then action708 -> PlayAction261, caller return main+0x7DE558; static PlayAction call main+0x7DE554 inside controller main+0x7DDD94 (+0x4C0).
Therefore the next unknown is controller invocation/mode, not P104B gate1/gate2.

P105A delta
Exactly two new whole-function trampolines:
- main+0x7DDD94 (+0x4C0 controller), ABI (actor, mode), void
- main+0x7E64D4 (+0x520 controller), ABI (actor, mode), void

Both hooks:
- capture X30 before any helper;
- preserve original actor and W1 mode;
- execute native Orig(actor, mode) exactly once on each runtime path;
- sample player side only;
- log focused actions 700..711;
- write no actor/action/state/gate/mode/control fields;
- never force 708 or 710;
- contain no char281 gameplay branch.

Log
[NSC:P105A] CTRL ... ctrl=4C0|520 phase=0|1 mode=... caller_off=... action=pre->post ...
phase=0 = controller ENTER, phase=1 = controller EXIT. seq pairs ENTER/EXIT for the same invocation.

Static anchors
+0x4C0 controller:
- entry 0x7DDD94
- mode comparisons at 0x7DDDC0 / 0x7DDDCC
- candidate selection MOV 262 at 0x7DE3A0, MOV 261 at 0x7DE3BC
- observed selected-action PlayAction callsite 0x7DE554 -> 0x766B8C

+0x520 controller:
- entry 0x7E64D4
- mode comparisons at 0x7E6504 / 0x7E6514
- MOV 710 at 0x7E6EA8
- PlayAction callsite 0x7E6EC4 -> 0x766B8C
- sole direct BL entry caller 0x488B28 (return 0x488B2C)

Test
One boot/session:
1. successful vanilla char91 UJ through cinematic;
2. failing custom Tobi UJ through 700 -> 707 -> 708 -> 261 -> 74.
Send the complete log and built artifact.

Analyze
python3 analyze_p105a_log.py uzuy_log.txt
