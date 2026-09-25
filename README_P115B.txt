P115B — Boot-safe cinematic event-type preflight provenance (READ ONLY)

Why P115B exists:
P115A used three new inline hooks. Runtime aborted during install with
AllocForTrampoline, so P115A is retired. P115B uses exactly ONE extra inline
hook at main+0x77C474 and does not intercept either C48 virtual call.

Probe:
  main+0x77C474 : native LDR W8,[X20,#0x50]

The hook faithfully reloads W8 from event+0x50, then logs the raw event type,
normalized type (raw & ~1), pass=(normalized==10), actor and peer identity.

Test:
  1) one successful vanilla UJ
  2) one Tobi own-UJ until absorb/stuck
  3) do not recover with shuriken/jutsu before saving log

Expected boot marker:
  [NSC:P115B] READY ... probe_ok=1

Decision:
  - no custom EVT_GATE: divergence is before main+0x77C474
  - custom EVT_GATE pass=0: event type gate is the first concrete divergence
  - custom EVT_GATE pass=1: event type is fine; next probe actor C48 only
