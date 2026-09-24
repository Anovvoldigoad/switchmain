# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R109

## P102A BUILD-FIX r2

GitHub Actions compile of the first P102A source package failed under `-Werror` because two stale P101 helper functions remained after the P101 state125 candidate was retired:

- `P101SetOp23Seen(void*, bool)`
- `P101QueryOp23Seen(void*)`

They were not referenced by P102A and therefore triggered `-Werror=unused-function`.

### Fix
- Removed both stale P101 helper functions.
- Removed obsolete `kP101Op23SeenBit` and its reset/clear operations.
- P102A functional logic is unchanged.
- P102A still reuses the existing P50 PlayAction trampoline and adds zero new trampolines.
- Exact gate remains: caller return `0x798F34`, requested action74, current action708, semantic UJ, generated OugiAwakening membership, E98=63, E9C=0, BDA4=1, BDC8=0, bounded to 16 suppressions.
- No force708/710, no actor action/state field write, no BDA4/E94 write, no char281 gameplay branch.

### Locked hashes
- paired patched main: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore vanilla main: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin: `229bbd6`

### Verification
`verify_p102a_source.py` PASS including explicit proof that the stale P101 helper symbols are absent and only `build-subsdk9-p102a.yml` is push-enabled.
