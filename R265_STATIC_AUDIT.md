# R265 Static Audit — Downstream Render Object Gate

## Hardware prerequisite from R264 / log39
R264 has now proven that the target native-ID46 carrier reaches the full secondary-preview and submit corridor:
- `data/ui/max/crsel/c/mtobcharsel.xfbin` file lookup is non-null.
- typed `nuccChunkAnm` key `mtobcharsel00` resolves non-null.
- `model+0x98` is populated non-null in Wait enter.
- character-select Draw reaches `main+0x5B3AC` repeatedly for identity 46.

Therefore the former hypotheses `secondary98 NULL`, `mtobcharsel00 missing`, and `Draw submit not reached` are retired.

## Exact downstream boundary
Clean Switch v1.70 `main+0x5B3AC` is a submit/dispatch function. It resolves one entry for the `(slot, identity)` pair and, for each non-null render object stored in that entry, calls `main+0x43F1F8`.

`main+0x43F1F8` is the first proven post-submit per-render-object gate. Its hard predicates are:
1. `object+0xDC != 0`;
2. `object+0xE0 != 0`;
3. `object+0xF8 <= 10`;
4. mode-specific condition from the native jump table;
5. `object+0x90 != NULL`;
6. float at `(object+0x90)+0x4C` compares non-zero;
7. only then branch through `(object+0x90)->vtable+0x50`.

The native mode jump table bytes at VA `0x1B376AB` are:
`[34,0,3,6,9,12,15,19,23,27,31]` for modes 0..10.
This decodes to:
- mode 0: unconditional mode-pass;
- mode 1: `+0xE4 == 0`;
- mode 2: `+0xE4 != 0`;
- mode 3: `+0xEC != 0`;
- mode 4: `+0xF0 != 0`;
- mode 5: `+0xF4 != 0`;
- modes 6..10: `+0x1B0 == mode`.

## R265 probe
R265 remains read-only and adds one new downstream hook at `main+0x43F1F8`. It is scoped only while the target ID46 Draw submit is executing.
For each reached object it records all native gate fields, pointer `+0x90`, the raw float bits at `+0x4C`, the final vtable target at `+0x50`, and a deterministic pre-gate PASS/FAIL classification.

Decision:
- `SUBMIT_END objects=0` -> submit lookup/entry has no render objects.
- `objects>0 gate_pass=0` -> exact render-object gate blocker is now localizable from fields.
- `objects>0 gate_pass>0` -> at least one object reaches the final native vcall; blocker moves downstream of `0x43F1F8`.
