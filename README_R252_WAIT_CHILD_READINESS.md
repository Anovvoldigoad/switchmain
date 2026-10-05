# NSC2Switch R252 — Wait Child Readiness Trace

Purpose: explain why the target model reaches `ccUiCharacterSelect3DModel` Wait state after R250 but the visual preview remains absent.

Read-only hooks:
1. target `mtobcharsel` registry capture (`main+0x1161B88`)
2. Wait enter (`main+0x549950`)
3. Wait update (`main+0x549B80`)
4. child readiness wrapper (`main+0x58498`)
5. child secondary wrapper (`main+0x58490`)
6. Wait consumer (`main+0x54ADE8`)

No CPK bind, no main patch, no gameplay patch, no ID patch, no path rewrite, no return override, no game-state mutation.

Deploy with the exact R250 `sound.cpk`; replace only diagnostic `subsdk9`.

Decision:
- `WAIT_READY_GATE result=0`: per-child readiness is the current blocker.
- ready=1 but `WAIT_SECONDARY_GATE result=0`: secondary owner/registry readiness is the current blocker.
- ready=1 + secondary=1 + `WAIT_CONSUME`: Wait child consumption is reached; inspect consumer/post-consumer visual attach next.
