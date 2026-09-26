NSC2Switch P120A — Generic Custom-UJ Cinematic Gate Bridge (Corrective A/B)
============================================================================
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Main Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39

WHY P120A EXISTS
----------------
P119A closed the read-only phase with direct producer -> victim-damage correlation:

Successful vanilla control:
  attacker char86 action707 EA4=0x834
  -> victim cursor126
  -> DAMAGE_ID_SPATK_BEGIN_DIRECT
  -> raw10
  -> cinematic gate PASS

Custom fixture:
  custom attacker action707 semantic=1 EA4=0x190
  -> victim cursor1848 / appended custom record
  -> raw15
  -> cinematic gate FAIL

  same attacker action707 EA4=0x1F4
  -> victim cursor1847 / appended custom record
  -> raw24
  -> cinematic gate FAIL
  -> natural 707->708 follows at EA4=0x258.

P118B already proved those cursor/index values are coherent and victim-owned. Therefore P120A does NOT patch B9E4, damageprm, session, state137, 708 or 710.

PATCH
-----
Exactly one new inline hook at main+0x77C474, replacing only:
  LDR W8,[X20,#0x50]

The callback first performs the native load. It substitutes W8=10 only when ALL are true:
  * current record index is in the appended custom damage range (>=1847 for locked v1.70);
  * coherent latest attacker snapshot exists and is fresh (P93 trace gap <=16);
  * attacker is a generic custom ID (>280,<0x1000), with no char281 special case;
  * attacker has semantic-UJ membership and is action707;
  * victim is valid and on the opposite side;
  * native raw type does not already pass the type10/11 cinematic gate;
  * the same attacker has not already been bridged during this action707.

The following native AND/CMP/B.NE remain unchanged. The latch resets when that attacker leaves action707.

IMPORTANT
---------
This is the first corrective A/B patch, not a claim that every future custom damage event should globally be type10. It changes only the register value consumed by this proven bucket5 gate under a narrow semantic custom-UJ guard.

NO gameplay hardcodes:
  * no char281 comparison
  * no DMG_MTOB_SPL00/01 string match
  * no fixed victim character

NO direct game-state writes:
  * no event record write
  * no actor+B9E4 write
  * no damage table write
  * no session creation/write
  * no action/state write
  * no force708/710

TEST
----
1. python3 verify_p120a_source.py
   Must end: P120A_DROPIN_SOURCE_VERIFY=PASS
2. git add -A
   git commit -m "P120A generic custom UJ cinematic gate bridge"
   git push
3. Download Actions artifact:
   NSC-P120A-custom-uj-cinematic-gate-bridge
4. Deploy main + subsdk9 from artifact on a clean v1.70 tree.
5. Fresh boot; verify:
   [NSC:P120A] READY ... patch_ok=1
6. Run one vanilla UJ control.
7. Run one custom Tobi Kamui UJ.
8. Observe both gameplay and full log.

CRITICAL MARKER
---------------
Expected custom trigger:
  [NSC:P120A] GATE ... bridge=1 ... aa=707 sem=1 ... appended=1 ... raw=<non10> out=10

SUCCESS CRITERIA
----------------
Strong PASS:
  * bridge=1 occurs exactly once during the custom action707;
  * victim proceeds into native cinematic instead of remaining trapped;
  * native action/session lifecycle continues without forced 710/state writes;
  * normal vanilla control remains unchanged.

Partial/FAIL interpretation:
  * bridge=1 but no cinematic: downstream C48/type9/outer setup becomes newly reachable; inspect that now-reached native corridor, do NOT return to B9E4 or damage table speculation.
  * patch_ok=0: deployment/fingerprint mismatch; do not test gameplay.
  * no bridge=1: one of the generic guards did not match; use GATE marker to identify which contract diverged.

P120A R135 v2 compile-only correction
------------------------------------
First R135 drop-in failed GitHub Actions compilation because the P120 callback used:
  exl::util::modules::GetMainModuleInfo()
Pinned exlaunch 229bbd6 declares the API as:
  exl::util::GetMainModuleInfo()
V2 changes only that namespace qualification. Runtime guards and gameplay behavior are unchanged.
The verifier now explicitly rejects the invalid namespace.
