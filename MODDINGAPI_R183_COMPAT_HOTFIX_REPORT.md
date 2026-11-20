# NSC2Switch R183 — ModdingAPI Compatibility Hotfix

## Trigger
R182 hardware report:
- new/custom characters can stall on the VS screen;
- Isshiki mod has multiple functions no longer working.

These are treated as R182 regressions until disproven.

## Root-cause priority
The most dangerous R182 change was the migration of the R181 eligibility gate from the proven fixed v1.70 fingerprint to an 8-word runtime signature resolver. `nsc_runtime_initialize()` returns false if R181 validation fails, which prevents all later installers from running. That can produce partial-runtime behavior: earlier patches are present while later CPK/gameplay hooks are absent.

A second compatibility risk was changing the mounted ModdingAPI CPK target from the proven `Tobi_Switch.cpk` path to a generic `NSC2Switch_ModPack.cpk` primary path.

## R183 decision
Preserve architectural refactor only; revert gameplay/content-sensitive migrations to the exact R181 source behavior:
- keep thin `main.cpp` bootstrap;
- keep `nsc_runtime_core` stable C ABI;
- keep package free of a loose game `main` override;
- restore R181 gate validation at `main+0x59CEB4` with the proven two-word fingerprint;
- restore R172 SetAnmDirect validation at the proven v1.70 offset;
- restore single proven ModdingAPI bind path `sim:data/moddingapi/Tobi_Switch.cpk`;
- defer generic ModPack/multi-pack binding until hardware compatibility is re-established.

## Test order
1. Cold boot with R183 `subsdk9` and no loose custom `main`.
2. Confirm new/custom character reaches battle from VS screen.
3. Confirm Isshiki functions that regressed in R182 are restored.
4. Confirm Tobi normal battle and UJ baseline.
5. Save full runtime log before any further resolver migration.
