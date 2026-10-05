# R252 static audit — Wait child readiness

Clean original Switch v1.70 `main` SHA256:
`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

## Wait update
Entry: `main+0x549B80`.

Recovered control flow:
- `[self+0x140] == 0` -> immediate exit.
- iterate pointer vector `[self+0x188, self+0x190)`.
- for each child, if `[child+0xE4] != 0`, skip it.
- otherwise call readiness wrapper `main+0x58498(child)`.
- wrapper `0x58498` is `child+8 -> main+0x1161D20`.
- readiness result 0 -> skip child, leaving `child+0xE4` unchanged.
- readiness result 1 -> call secondary wrapper `main+0x58490(child)`.
- wrapper `0x58490` is `child+8 -> main+0x1161C98`.
- if secondary returns nonzero, Wait update calls consumer `main+0x54ADE8(self, child+0xB0, child+0xE0)`.
- regardless of secondary success/failure after the readiness gate passes, native writes `1` to `[child+0xE4]`.

Exact callsites:
- `main+0x549BF0 -> main+0x58498`
- `main+0x549BFC -> main+0x58490`
- `main+0x549BC8 -> main+0x54ADE8`

Therefore R252 traces the earliest decisive per-child split instead of adding another broad state tracer.
