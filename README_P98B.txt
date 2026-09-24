NSC2Switch P98B — State125 Request Provenance Trace

Corrected custom UJ graph:
  700 -> 707 -> 708 -> 710 -> cinematic

Why P98B:
- P97A is retired: suppressing 708 removed the original stick but prevented the required 708 phase.
- P96 native run proves that while action708 is active, E9C changes 0 -> 125 at EA4~0x5DC.
- State125 then commits (E94=125, BDA8=1) and the downstream handler requests action261 from main+0x7DE554, followed by neutral74.
- Therefore action261 is downstream. The earliest proven wrong fork is the state125 request during action708.

Static proof:
- State-request virtual slot is actor vtable+0xE28.
- 155 native vtables map +0xE28 to main+0x7A89A4; one subclass override maps it to main+0x138D14.
- Historical runtime custom actor vtable is main+0x201BF58. Pinned relocation mapping for that exact table:
    +0xE28 -> 0x7A89A4
    +0xE40 -> 0x7B468C (runtime-proven MODE_BASE)
    +0xEB0 -> 0x772594 (runtime-proven PlayAction wrapper)
- main+0x7A89A4 writes requested W1 to actor+E9C at main+0x7A89F0 after native validation.

P98B behavior:
- Restores P96/native 707->708 behavior; P97 guard is absent.
- Adds one read-only provenance trampoline at whole function main+0x7A89A4.
- Orig() is called exactly once with unchanged args; no state/action/control write is introduced.
- Logs requested state, arg2/arg3, caller return/call instruction, actor vtable+E28 target, and pre/post action/E94/E98/E9C/EA4/EA8/BDA4/BDA8/BDC8.

Runtime test:
1. One custom UJ through 707 -> 708 until it falls out. Vanilla is optional for this provenance run.
2. Send full uzuy log + compiled artifact.

Decisive outcomes:
A. `[NSC:P98B] STATE_REQ ... req=125 ... action=708` appears:
   caller_off is the exact producer to disassemble/fix next.
B. E9C becomes125 in P93/P95 logs but there is NO P98B req=125:
   state125 bypasses vslot/base 0x7A89A4; pivot directly to 0x7A8A9C/non-virtual writer provenance.

Never hardcode char281; it is only the reproducer. No force708/710 and no E9C write.
