NSC2Switch P54A — DIRECT JUTSU OWNER PROBE (Switch v1.70)
============================================================

WHY P54A EXISTS
P53A hardware result locked a new fact: pressing XXA with Tobi True Awakening
visibly produces a normal jutsu, but the existing PlayAction hook does NOT see
PlayAction(84), SPTYPE930, or UJ 700..740 for Tobi. Therefore the awakened
jutsu path bypasses the assumed PlayAction route.

STATIC v1.70 RE RESULT
In the same CtrlAct/skill cluster, two controller functions bypass PlayAction
and call actor vtable+0xF98 directly:

  owner 0x2A472C -> direct action 98 at 0x2A50C4/0x2A50D4
  owner 0x2A51B8 -> direct action 100 at 0x2A5698/0x2A56A8

Both owners have an actor/mode controller ABI. P54A hooks ONLY their function
entries and logs PRE/POST state. It never changes mode, current action, return
state, actor fields, or input state.

ACTIVE RUNTIME HOOKS
Inherited hardware-proven P50A core (5):
  0x473190 CpkBind
  0x816300 Event236 compatibility
  0x766B8C PlayAction route probe
  0x754A80 ConditionGetter
  0x8134F8 Event121 SELF compatibility

P54A read-only additions (2):
  0x2A472C DirectAction98 owner
  0x2A51B8 DirectAction100 owner

TOTAL = 7 trampolines.

NO GAMEPLAY PATCH
- no charID==281 branch
- no Danzo/57 branch
- no COND_2DNZ executable branch
- no 708->710 forcing
- no UJ forcing
- no input rewrite
- no A33C60 NOP

PLAYACTION ROUTE OBSERVATION
Existing PlayAction hook additionally labels 98, 100, 937 and 938 if any of
those ever travel through PlayAction; direct owner calls still bypass it.

EXPECTED BOOT MARKERS
  [NSC:P50A] READY ... installed_trampolines=5 ...
  [NSC:P54A] READY inherited_p50=1 direct_owner_probe=1 added_trampolines=2 total_trampolines=7 ...

HARDWARE TEST
1. Naruto control: press XXA once.
2. Start a fresh battle as Tobi True Awakening.
3. Press XXA once or twice. Do not deliberately press XA separately.
4. Send the complete Uzuy log.

DECISION
- DIRECT98_OWNER char>280 around the visible jutsu -> awakened fallback owner is
  0x2A472C; inspect its mode jump-table gate and upstream selector next.
- DIRECT100_OWNER char>280 -> same, owner 0x2A51B8.
- neither owner -> the fallback uses another direct-setter family; P54 result
  eliminates these two candidates and the next probe moves to the remaining
  action-setter selector, without touching gameplay.
- ACTION_ROUTE UJ index=700 for the custom actor -> UJ promotion became live;
  resume 700->707->710 progression analysis.

PAIRING
Use the main emitted with this kit/artifact. It is the same P50A paired main;
do not combine subsdk9 with a different experimental main.
