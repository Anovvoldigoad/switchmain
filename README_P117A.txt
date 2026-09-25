P117A — Action-event stream census at bucket5 dispatcher boundary (READ ONLY)

Purpose
- P116 proved successful vanilla reaches main+0x7EF098 from bucket5 and creates session9/session10.
- In the same run, custom Tobi char281 never reaches main+0x7EF098 at all.
- P117 moves upstream to the bucket5 action-event dispatcher and asks whether the native event type 10/11 is present for vanilla but absent for custom Tobi.

Runtime hook
- Exactly one whole-function trampoline: main+0x3F4BC0.
- Only calls returning to main+0x77B5AC are logged.
- At that exact callsite, X0 still contains the current event pointer resolved by main+0x3F4B00.
- Non-focused calls immediately execute Orig(event_x0) with no extra event reads/logging.
- Focused calls read event+0x28, +0x48 and +0x50, then execute Orig(event_x0) exactly once.

Important native corridor
- dispatcher entry main+0x77B560
- event lookup call main+0x77B590 -> 0x3F4B00
- event-gate getter call main+0x77B5A8 -> 0x3F4BC0; return 0x77B5AC
- event type gate main+0x77C474: (raw_type & ~1) == 10, i.e. raw type 10/11
- bucket5 outer call main+0x77C5E8 -> 0x7EF098

Log
[NSC:P117A] EVENT n=... event=... caller_off=0x77b5ac raw_type=... norm_type=... type10_11=... gate_ret=... payload28=... mask48=...

Decision
- vanilla UJ has type10_11=1 but custom Tobi window has none:
  missing upstream action-event stream/descriptor is the root frontier.
- both have type10_11=1:
  next probe is one C48 readiness gate at a time.
- neither has clean type10/11 comparison:
  do not force state/session; inspect exact event sequence and test fixture.

Test
1. One vanilla UJ that reaches cinematic/710.
2. One Tobi own-UJ until opponent is absorbed/stuck.
3. Do not recover with shuriken/jutsu.
4. Wait a few seconds, exit, collect full log.
