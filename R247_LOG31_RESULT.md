# R247 hardware result — uzuy_log(31).txt

Log identity:
- bytes: 1075261
- SHA256: 997ce0813cf6d9c661fb1ad944eda49f1abe06c7d79db502bef030097a8877dd
- R247 READY: PASS, read-only, 9 hooks.

Target-only state-table counts:
- target STATE_CALL events: 1026
- Load enter post: 1
- Load update post: 4
- Create enter pre/post: 1 / 1
- Create update pre/post: 508 / 507
- target Wait events: 0
- target Select events: 0
- target state5c=3 observations: 0

Decisive chronology:
1. target registry is captured for `data/ui/max/crsel/c/mtobcharsel.xfbin`;
2. target Load update advances `state5c 1 -> 2`, `phase6c 0 -> 1`;
3. target Create enter runs and produces non-null `modelB0=0x3abf9d6000`;
4. target Create update then repeats for the remainder of the hover with `state5c=2`, `phase6c=0`;
5. target never reaches Wait or Select before shutdown.

Locked interpretation:
- Load / registry readiness: PASS and retired.
- post-Load scheduler dispatch into Create: PASS.
- Create::enter model allocation/construction: PASS_NON_NULL.
- Create::update readiness: FAIL_STUCK_STATE2.
- current boundary is inside the model readiness producer consumed by `main+0x54991C`.

Static follow-up on clean v1.70 main:
- Create::update `main+0x54991C` loads `[self+0xB0]` and calls `main+0x6ECBB0`.
- `main+0x6ECBB0` is exactly `return *(void**)(model+0x90) != nullptr`.
- Create::enter calls model init `main+0x6EAC24`.
- model init loads `model+0x38`, calls `main+0x3F4130(identity)`, and branches directly to epilogue `main+0x6EB018` on null.
- the successful path later stores a newly created object to `model+0x90` at `main+0x6EAD98`.

NEXT=R248_CREATE_IDENTITY_READINESS_TRACE
