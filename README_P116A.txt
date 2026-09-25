P116A — Universal cinematic outer-caller census (read only)

Why this exists:
P114/P115 inspected the 0x77C5E8 upstream corridor, but a later successful vanilla UJ reached 710 without executing the 0x77C474 event gate. Static scan of paired main v1.70 proves 0x7EF098 has six direct BL callers, so 0x77C5E8 is not universal.

P116A installs one known-boot-safe whole-function trampoline at main+0x7EF098 and records the incoming caller return address/bucket. It also records actor/peer state and session9/session10 before/after native Orig(actor).

Static direct callsites -> main+0x7EF098:
  0x0D6BDC (return 0x0D6BE0, bucket1)
  0x0FBF60 (return 0x0FBF64, bucket2)
  0x32F570 (return 0x32F574, bucket3)
  0x753CB8 (return 0x753CBC, bucket4)
  0x77C5E8 (return 0x77C5EC, bucket5)
  0x802634 (return 0x802638, bucket6)

No state/action/session is forced or created manually. Orig(actor) is called exactly once.

Test:
1) one successful vanilla UJ
2) one Tobi custom own-UJ until absorb/stuck
3) no recovery shuriken/jutsu
4) save full log

Expected decisive output:
- vanilla: [NSC:P116A] CALL ... s10=0->1 and exact caller bucket
- custom Tobi: either no CALL (missing upstream producer) or a CALL with no s10 creation (inner failure)

R130 WORKFLOW HOTFIX
- Runtime P116A code is unchanged from R129.
- Explicitly overwrites stale `.github/workflows/build-subsdk9-p115b.yml` as workflow_dispatch-only.
- Re-run `python3 verify_p116a_source.py`; only P116A may be push-enabled.
- Use shell `&&` chaining so a failed verifier prevents commit/push.
