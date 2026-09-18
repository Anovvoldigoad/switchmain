NSC2Switch P48B — MINIMAL 707/708 ACTION-DECISION PROBE
Target: Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
Known target Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39

WHY P48B EXISTS
P48A failed before game boot. The supplied Uzuy log proves exlaunch aborted in
source/lib/hook/nx64/hook_impl.cpp while installing a trampoline:
  Failed: AllocForTrampoline(&rxtrampoline, &rwtrampoline)
P47 installed 21 trampoline hooks. P48A raised this to 24.
P48B removes the unrelated historical trace hooks from installation and installs
ONLY 3 trampoline hooks total.

INSTALLED HOOKS
  0x473190 CpkBind       : bind Tobi_Switch.cpk fixture
  0x766B8C PlayAction    : PRE/POST action + return
  0x768E84 ActionLookup  : requested index, flag, pointer/null result

NOT INSTALLED
All older file-load, event, lifecycle, stage, Ougi-finish, event236, and other
diagnostic hooks remain in source only for continuity. They are deliberately not
installed and therefore consume no trampoline entries.

SAFETY
- No writes to actor/action state in the active decision probes.
- No charID==281/Tobi gameplay branch.
- All 3 installed hook sites are fingerprint-checked against Switch v1.70 first.
- The CPK bind behavior is inherited from the already-booting P47 baseline.

FIRST TEST
1. Replace P48A subsdk9 with P48B.
2. Boot game only.
3. Confirm log contains:
     [NSC:P48B] READY cpk=1 decision=1 installed_trampolines=3
4. If boot succeeds, run:
   A) Tobi UJ once
   B) working vanilla control UJ once
5. Save complete nxlink/Uzuy log.

DECISIVE EXPECTATION
Hypothesis under test:
  Tobi:    PlayAction(707)=1; lookup(708,1)=NON-NULL; diverts to 708.
  Vanilla: PlayAction(707)=1; lookup(708,1)=NULL; reaches 710 chain.

STAGED FOLLOW-UP
ActionGate 0x769A4C and ActionRemap 0x769B04 are intentionally NOT installed in
P48B. Add them only after the single new ActionLookup hook has been proven boot-safe.

ANALYSIS
  python3 analyze_p48b_log.py <log.txt>

DO NOT
- Do not use P48A again.
- Do not patch 708->710.
- Do not hardcode char 281.
