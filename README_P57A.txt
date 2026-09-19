NSC2Switch P57A — CENTRAL ACTION SETTER PROVENANCE TRACE

PURPOSE
P56B rejected the scanned contiguous PC-style boolean control-block model.
P57A does not guess another actor offset. It hooks the proven central action setter
behind actor vtable+0xF98 at Switch v1.70 main+0x766320 and records every action
request for generic custom actors, plus vanilla UJ 700..740 control traffic.

WHY THIS BOUNDARY IS PROVEN
- P56B/P55 runtime: vanilla PlayAction 700..740 reports vtable+0xF98 target main+0x766320.
- PlayAction 0x766B8C calls vtable+0xF98 with actor/index/a2/a3 and immediately
  continues without consuming a return value.
- 0x766320 prologue saves w3,w2,x0,w1 into callee-saved regs, proving the 4-arg ABI.

ACTIVE HOOKS = 6
1 CpkBind 0x473190
2 Event236 0x816300
3 PlayAction 0x766B8C
4 ConditionGetter 0x754A80
5 Event121 0x8134F8
6 CentralActionSetter 0x766320

P57A IS DIAGNOSTIC ONLY
- no action rewrite
- no input rewrite
- no actor-control-field write
- no 708->710 force
- no Tobi/281 gameplay branch
- custom filtering is generic charID > 280 && < 0x1000 and affects logging only

DECISIVE LOG
[NSC:P57A] SETTER ... char=281 requested=<actual action> ... caller_main=1 caller_off=0x...

caller_off is the return address (LR) inside main; the callsite is normally caller_off-4.
call_m4 is the instruction at that callsite and call_m8 is the preceding instruction.

TEST ORDER
1. Naruto vanilla: successful XXA/UJ once as control.
2. Fresh match Tobi True Awakening. Stand still if possible.
3. Press XXA 2-3 times until the wrong ordinary jutsu is visibly produced.
4. Close emulator and send full log + build artifact.

INTERPRETATION
- If a Tobi SETTER row appears at each wrong-jutsu attempt, requested+caller_off identify
  the exact controller/selector branch to reverse next.
- If no custom setter row occurs at the visible jutsu attempt, then the effect is not being
  started by the actor action setter; next trace must move to the skill/effect controller.
Do not infer either result before hardware data.
