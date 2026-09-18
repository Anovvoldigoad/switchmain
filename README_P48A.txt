NSC2Switch P48A — 707/708 ACTION-DECISION PROBE (LOG-ONLY)
Target: Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
Known target Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39

PURPOSE
P47A proved PlayAction(707) returns 1 for both Tobi/custom and working vanilla.
Static RE then found a separate state-machine path that can transition current action 707 -> 708 through:
  0x769A4C completion/timing gate
  0x768E84 action lookup/availability resolver
  direct vtable+0xF98 setter (bypasses PlayAction wrapper)
P48A measures that decision chain without changing gameplay state.

NEW LOG-ONLY HOOKS
  0x766B8C PlayAction: PRE + POST action state and return value
  0x768E84 ActionLookup: requested index, flag, pointer/null result, PRE/POST action
  0x769A4C ActionGate: current action and bool-like return
  0x769B04 ActionRemap: requested index -> resolved index

SAFETY / SCOPE
- No writes to actor/action state in P48A probe code.
- No Tobi/281 conditional behavior in decision hooks.
- Existing mod CPK fixture path remains inherited from the prior bridge and is unrelated to the decision-probe logic.
- All four critical probe hooks are guarded by exact 8-word v1.70 fingerprints before installation.

TEST MATRIX (minimum)
A. Tobi/custom character: perform UJ once without extraction trick.
B. Tobi/custom character: perform UJ once with the known Katon/extract setup if useful for comparison.
C. Working vanilla control (same vanilla character used for P47/R56 if possible): perform UJ once.
Capture complete nxlink output from READY through battle/UJ completion or hang.

DECISIVE EXPECTATION
Working hypothesis:
  Tobi:    PlayAction(707)=1; gate(707) eventually=1; lookup(708,flag=1)=NON-NULL; path diverts to 708; 710 chain absent.
  Vanilla: PlayAction(707)=1; gate(707) eventually=1; lookup(708,flag=1)=NULL; later 710->711->712->713->714->740 occurs.
This is a hypothesis to test, not baked into the hook behavior.

ANALYSIS
  python3 analyze_p48a_log.py <log.txt>

BUILD
GitHub workflow uses devkitpro/devkita64 and pinned exlaunch commit 229bbd6, same baseline as P47A.
Run workflow: Build NSC P48A action decision probe.
