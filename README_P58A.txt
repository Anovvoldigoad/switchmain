NSC2Switch P58A — PLAYACTION CALLER TRACE

WHY P58A EXISTS
P57A produced the first concrete runtime provenance for the visible Tobi failure:
- Tobi char281 requests action445 twice, each time 74 -> 445, then returns 445 -> 74.
- The central setter LR for both 445 requests is main+0x766BD4.
- Static v1.70 disassembly proves 0x766BD4 is INSIDE PlayAction 0x766B8C, immediately
  after its BLR to actor vtable+0xF98 at 0x766BD0.
Therefore P57A proved action445 goes through PlayAction; it did NOT yet reveal which
controller/selector called PlayAction. Earlier P53/P55 logs missed 445 only because their
PlayAction logging filter did not include index445.

P58A closes exactly that one provenance gap.

ACTIVE HOOKS = 6 (UNCHANGED FROM P57A)
1 CpkBind 0x473190
2 Event236 0x816300
3 PlayAction 0x766B8C  [P58 caller trace added inside existing hook]
4 ConditionGetter 0x754A80
5 Event121 0x8134F8
6 CentralActionSetter 0x766320 [P57 cross-check retained]

GAMEPLAY DELTA
NONE.
- no action rewrite
- no input rewrite
- no actor-field/control-field write
- no UJ force
- no 708->710 rewrite
- no char281 gameplay branch
P58 custom filtering affects logging only and remains generic charID>280 && charID<0x1000.

DECISIVE MARKER
[NSC:P58A] PLAY_CALL ... char=281 index=445 ... caller_main=1 caller_off=0xXXXX callsite_off=0xYYYY ...

If caller_main=1, callsite_off is caller_off-4 and identifies the exact native BL to
PlayAction that selected action445. Disassemble that caller before changing gameplay.

P57 HARDWARE FACTS LOCKED
- vanilla129: setter requests 700,707,710,711,712,713,714,740.
- custom281: setter requests 74,74,445,74,445,74,74.
- 445 rows: pre=74 post=445, then ~1.8s later 74 is requested from pre=445.
- P57 central-setter LR for 445 = main+0x766BD4, i.e. PlayAction wrapper internal return.

STATIC 1.70 PLAYACTION CALLSITE CENSUS
There are several plausible callsites that can feed action445. Examples include direct literal
445 at main+0x1EEAC0, +0x64199C, +0x807574 and helper-resolved variants. Do NOT choose one
by proximity/string heuristics. P58 hardware caller_off is the discriminator.

TEST (MINIMAL, TO AVOID TIMING AMBIGUITY)
1. Fresh match Tobi True Awakening.
2. Stand still; do not press XA separately.
3. Press XXA exactly TWO times, waiting until each wrong ordinary jutsu fully finishes.
4. Close emulator and send full log + P58 build artifact.
Optional: one Naruto vanilla UJ before the Tobi match is useful as a caller-trace control,
but not required if the Tobi PLAY_CALL rows have caller_main=1.
