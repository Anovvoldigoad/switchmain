NSC2Switch P112A — exact state125 producer entry provenance (READ ONLY)
Target: STORM CONNECTIONS Switch v1.70 / main Build ID 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Parent: P96 runtime + P50 victim-safe + P89 admission.

WHY P112A
P111 proved successful vanilla victim admission is req125 -> req126 -> PlayAction12 before the type10 cinematic manager. Failing Tobi own-UJ victim instead takes state39 -> 121 and never reaches victim req125/126/12. The same native whole function main+0x7EB270 is known to request state125, and later the failing attacker Tobi also reaches it at action708 as cleanup. P112A traces the ENTRY of that whole function so the incoming caller and actor target are proven rather than inferred.

WHAT IT DOES
- One whole-function trampoline at main+0x7EB270.
- Captures x30/LR before helper calls.
- Logs target actor side/char/action/state and native enemy/peer context via existing vslot +0xDD0 getter.
- Calls Orig(actor) exactly once, unchanged.
- Logs actor post-state.
- No state mapping, no action force, no manual call to 0x7EB270, no char281 branch.

TEST
1) Boot and confirm: [NSC:P112A] READY ... probe_ok=1
2) Perform ONE vanilla UJ that reaches cinematic successfully.
3) Perform ONE Tobi own-UJ and let it fail naturally through the Kamui absorb/stuck/fallback path.
4) STOP. Do not use the stage-switch recovery jutsu before saving the log. That later recovery was useful information, but it adds unrelated state121 noise.
5) Upload the compiled P112A artifact + full Uzuy log.
Optional local analyzer: python3 analyze_p112a_log.py uzuy_log.txt

DECISION
- Vanilla victim ENTRY exists; custom Tobi victim ENTRY absent; custom attacker action708 ENTRY exists => caller of vanilla victim entry is the missing native victim-admission producer frontier.
- Custom victim ENTRY exists but fails downstream => compare caller/post-state inside 0x7EB270.
- Same caller but actor role differs => target-selection immediately before the call is the root frontier.

Do not re-enable P107/P108 state forcing.
