# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R130

## P116A workflow hotfix

Runtime/gameplay instrumentation is unchanged from P116A R129.

R129 source verifier correctly detected that a stale P115B GitHub Actions workflow remained push-enabled in an existing repository after overlaying the drop-in kit. Because absent files are not deleted by an overlay, R130 now ships an explicit `.github/workflows/build-subsdk9-p115b.yml` manual-only disabled stub (plus the root mirror) so applying this kit overwrites the stale P115B workflow.

Required invariant after overlay:

`push_enabled_workflows ['build-subsdk9-p116a.yml']`

P116A runtime target remains one whole-function trampoline at `main+0x7EF098`, read-only, with six direct caller buckets and no state/session forcing.
