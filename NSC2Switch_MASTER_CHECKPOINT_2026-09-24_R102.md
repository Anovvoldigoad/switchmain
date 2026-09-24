# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R102

## P98B CI packaging correction

P98B runtime design remains unchanged from R101:
- native custom UJ path restored: 700 -> 707 -> 708;
- P97 early-transition guard is not installed;
- one read-only provenance hook at main+0x7A89A4 traces state requests, especially requested state 125 while action708 is active;
- no state writes, no force708, no force710, no char281 gameplay branch.

## CI failure observed

`verify_p98b_source.py` correctly reported:

`push_enabled_workflows ['build-subsdk9-p97a.yml', 'build-subsdk9-p98b.yml']`

Root cause: the first P98B package did not contain `build-subsdk9-p97a.yml`, so an older P97A workflow already present in the repository remained push-enabled after the P98B drop-in.

## R102 correction

P98B v2 now also ships `.github/workflows/build-subsdk9-p97a.yml` as manual-only (`workflow_dispatch` only). This overwrites the stale push-enabled P97A workflow when the kit is copied into the repository.

No gameplay/source logic was changed.

Verified result:
- `push_enabled_workflows ['build-subsdk9-p98b.yml']`
- `P98B_DROPIN_SOURCE_VERIFY=PASS`

Next runtime objective is unchanged: capture `[NSC:P98B] STATE_REQ ... req=125 ... action=708 ... caller_off=...` to identify the exact producer of state125 in the 708 -> 710 failure corridor.
