# R251 / log35 hardware result — R250 data + R247 state-table tracer

Input log: `uzuy_log(35).txt`.

Locked hardware facts:
- R247 read-only tracer installed successfully.
- Target `mtobcharsel` registry was captured.
- Target Load advanced `state5c 1 -> 2` / `phase6c 0 -> 1`.
- Target Create entered with a non-null model and Create update advanced `state5c 2 -> 3` / `phase6c 0 -> 1`.
- Therefore the R250 `bod1` internal-identity fix materially resolved the former Create-readiness blocker.
- Target then entered Wait (`state5c=3`).
- Target Wait update remained `state5c=3 / phase6c=0` for >16.7 seconds (about 77.787s through at least 94.552s).
- No `Select` callback was observed in the run.

Current frontier:
`WAIT_STATE_ENTERED_AND_STABLE`.
The next diagnostic boundary is inside `ccUiCharacterSelect3DModel::Wait::update @ main+0x549B80`, specifically its per-child readiness path.

Do not reopen:
- R250 bod1 chunk identity;
- Create readiness;
- registry/load state;
- ID46 identity lookup;
- ID281 numeric admission.
