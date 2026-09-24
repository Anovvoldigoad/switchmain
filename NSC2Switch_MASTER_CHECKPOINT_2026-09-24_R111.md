# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R111

## P103A BUILD-FIX R2 — workflow/verifier correction only

Parent functional candidate: P103A SpecialCond factory selector bridge.

Functional gameplay logic is unchanged from R110:
- generic generated specialCond map;
- Tobi compiled charID 281 maps to dispatcher selector 58 (`COND_2DNZ`);
- factory dispatcher hook at main+0x7CAB00;
- original context argument preserved;
- actor identity is not rewritten;
- no action/state writes;
- no force708/710;
- P50 victim-safe Event236 and P89 admission baseline preserved;
- P102 HOLD74 and P101 state125 guard remain absent.

### Why R110 CI failed

R110 verifier incorrectly asserted that `.github/workflows` physically contained only `build-subsdk9-p103a.yml`.
A long-lived repository legitimately still contained historical P87–P102 workflow files, so preflight failed before compilation despite all source/fingerprint checks passing.

### R111 correction

- Verifier now checks **push-enabled workflows**, matching the robust P102 verifier model.
- Historical P87–P102 workflows are retained but normalized to `workflow_dispatch` only.
- Exactly `build-subsdk9-p103a.yml` remains push-enabled on `main`.
- No C++ gameplay logic changed.

Expected verifier tail:

```text
push_enabled_workflows ['build-subsdk9-p103a.yml']
P103A_DROPIN_SOURCE_VERIFY=PASS
```

This is a packaging/build-system fix only; runtime hypothesis and test interpretation remain R110.
