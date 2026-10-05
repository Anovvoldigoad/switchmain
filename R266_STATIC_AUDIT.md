# R266 Static Audit — Exact Render Registration Producer Chain

## Why R266 exists

R265 hardware (`uzuy_log(40).txt`) proved that character-select Draw reaches `main+0x5B3AC` for `(slot=0, identity=46)` but the submit resolves zero render objects on every bounded frame.

Offline clean-main disassembly narrows the missing producer chain.

## Submit table layout at main+0x5B3AC

`main+0x5B3AC` uses a two-level tree/map under `draw_ctx+0x20`:

1. outer lookup key = `slot` (R265 target: 0)
2. inner lookup key = `identity` (R265 target: 46)

The inner entry owns:

- `entry+0x40` — pointer to an 11-element render-object pointer array
- `entry+0x48` — initialized element/count field (native producer writes 11)

The lookup helpers at `0x5D514` / `0x5D650` behave as creating/operator[] style lookups. Draw can therefore create an empty entry even when no earlier registration producer populated it.

## Native producer at main+0x594D8

`main+0x594D8` is the shared registration producer. For a new `(slot, identity)` entry it:

- allocates `0x58` bytes = 11 x 8-byte pointer slots,
- stores the pointer at `entry+0x40`,
- writes `11` to `entry+0x48`,
- zero-initializes all 11 pointer slots,
- then resolves/constructs the actual render objects.

Its first eligibility predicate is `main+0x5E998`.

## Base-character callsite

The base model path calls the same producer at `main+0x6ED424` from the registration bridge `main+0x6ED110` with:

- producer slot `w6 = 0`,
- producer identity `w7 = [descriptor+4]`,
- base object `[model+0x90]`.

For the R250/R263 diagnostic fixture this should become exactly `(slot=0, identity=46)`.

## Internal model registration-child vector

The bridge is driven by an internal model vector:

- begin `model+0x2B38`
- end `model+0x2B40`
- capacity `model+0x2B48`
- initialized flag `model+0x2B68`
- mode/context `model+0x2B6C`

`main+0x6ECEE8` constructs/appends 0xE8-byte child descriptors into this vector.
`main+0x6ED558` traverses the vector and calls `main+0x6ED110` only after the child's native readiness predicates pass.

## R266 decision tree

R266 is read-only and traces exactly five new boundaries while retaining the proven target/submit chain:

- `0x6ECEE8` model child creation
- `0x6ED558` registration tick/vector census
- `0x6ED110` registration bridge
- `0x594D8` render producer
- `0x5E998` producer guard

Interpretation:

- `child_count=0` -> internal render-registration child vector is empty.
- `child_count>0` but no `REG_BRIDGE` -> child readiness prevents registration.
- `REG_BRIDGE` but no target `RENDER_PRODUCER` -> resource/manager gate inside bridge.
- producer reached + `PRODUCER_GUARD result=0` -> exact producer eligibility guard blocks.
- guard passes but R265 submit remains objects=0 -> failure is after the guard in source-index or render-object fill.
