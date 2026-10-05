# R267 Secondary Inner Base Draw Trace

Read-only diagnostic for the actual character-select base-body draw path.

Use with the exact R263 `sound.cpk` carrier and clean game `main`.

Key markers:

- `[NSC:R267] INNER_BIND_PRE/POST`
- `[NSC:R267] BASE_DRAW_PRE/POST`
- `[NSC:R267] BASE_VISUAL_DRAW`

Decision:

- `typed_inner08=0` and `post_inner18=0`: typed `mtobcharsel00` exists but its inner animation/model binding is missing.
- `inner18!=0` but no `BASE_VISUAL_DRAW`: base draw call predicate/control flow is unexpectedly blocked.
- `inner18!=0` and `BASE_VISUAL_DRAW` occurs: frontier moves downstream of `main+0x117E0D8`.
