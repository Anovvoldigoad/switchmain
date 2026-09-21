# R71 / P62A — Persistent UJ Control Getter

## Locked hardware evidence
P61A hardware run: READY=1, guarded F58 overrides=0, custom Play700=0, custom Play445=3; victim-UJ remains safe.

## Root semantic correction
MovesetPlus `me_enable_control` is an enable/disable semantic, not a one-shot backing-store write. P60 proved one-shot Switch selector8 writes succeed but later return to zero before the failing route is corrected. P62 therefore virtualizes only selector8 reads for an exact source-enabled custom actor until matching source disable.

## Functional delta
`main+0x7C6280` native getter trampoline. Original result wins unless all are true: raw==0, selector==8, control object maps exactly to a currently valid custom actor, and that actor is registered by source op14 p2=0 p3=1. Then P62 returns 1. No gameplay field is written by the getter hook.

## Rejected paths
- P61 F58 false->true override: rejected by hardware (0 overrides).
- Direct state 0x87 write: forbidden.
- PlayAction 445->700 rewrite: forbidden.
- Tobi/281 hardcode: forbidden.
- rejected historical actor+0x12A24 control layout: forbidden.

## Expected decisive runtime
If custom XXA enters the native UJ router far enough to query selector8 while source UJ enable is active, log must contain `[NSC:P62A] CTRL_GET_UJ_PERSIST`, ideally with caller_off 0xC7934 and/or 0xC79B0. Success still requires custom `PLAY_CALL index=700`; the getter marker alone is not declared a fix.
