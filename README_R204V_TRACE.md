# R204V — ccUiCharacterSelect3DModel post-registry state-gate trace

R204V exists because R204J + R238A hardware proved the primary mtob charsel registry reaches `REGISTRY_PROCESS result=1`, while the preview remains empty and no target RESOURCE_LOOKUP/CHUNK follows.

Historical dedup gate: no earlier checkpoint contains a tracer for the native function at `main+0x549804`. R204E explicitly named this state gate as the next boundary if consumption stayed absent.

Static v1.70 path at `main+0x549804`:

- process registry at `[state+0xA8]`; if 0 -> return
- if `[state+0xC0]` exists, process its registry through `main+0x58490` -> `main+0x1161C98`; if not ready, consult `main+0x58498` -> `main+0x1161D20`
- process secondary registry loaded from `[[state+0x80]-0x18]`; if 0 -> return
- only after all gates pass: write `[state+0x6C]=1`, `[state+0x5C]=2`

R204V installs four read-only trampolines only:

1. owner register `0x1161B88` to learn the exact mtob charsel primary registry;
2. registry process `0x1161C98`;
3. registry-state helper `0x1161D20`;
4. charsel state gate `0x549804`.

No CPK bind, main patch, gameplay patch, ID patch, path rewrite, forced return, or state mutation is performed by R204V.

Decisive markers:

- `GATE_REGISTRY role=primary result=1` then another `GATE_REGISTRY ... result=0`: secondary registry is the blocker.
- `GATE_REGISTRY_STATE ... result=0`: helper/state predicate blocks progression.
- `GATE_EXIT ... advanced=0`: one of the logged gates prevented the native state commit.
- `GATE_EXIT ... s5c=...->2 s6c=...->1 advanced=1`: registry/state gating fully passes; move downstream to preview actor/model construction.
