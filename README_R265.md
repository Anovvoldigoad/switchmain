# R265 — Downstream Render Gate Trace

Use with the exact R263 `sound.cpk` diagnostic carrier and clean `main`.
Replace only diagnostic `subsdk9` with the R265 artifact.

Expected markers:
- `[NSC:R265] READY ...`
- `[NSC:R265] SUBMIT_BEGIN ...`
- `[NSC:R265] RENDER_GATE ... pass=0/1`
- `[NSC:R265] SUBMIT_END ... objects=N gate_pass=M`

The probe is read-only. It does not rewrite paths, IDs, returns, state, gameplay, CPK bindings, or `main`.
