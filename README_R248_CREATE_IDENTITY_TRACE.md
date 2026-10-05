# NSC2Switch R248 — Create Identity / Readiness Trace

R248 follows R247 hardware on the unchanged R245C real-Tobi native-ID46 carrier.

R247 proved the target reaches Load state2 and enters Create, with a non-null model object, but Create::update stays state2 for the remainder of the hover. Static recovery shows Create::update advances only when model+0x90 becomes non-null.

R248 traces the native producer chain that can populate model+0x90. It is diagnostic/read-only only.

Deploy:
- exact R245C carrier/data setup used for R247;
- clean original main;
- external Tobi_Switch.cpk OFF;
- ID281 patch OFF;
- replace only diagnostic subsdk9 with the R248 artifact.

Expected artifact: `NSC2Switch-R248-CREATE-IDENTITY-READINESS-TRACE`.

Test: cold boot, hover working vanilla briefly, then native-ID46/Tobi for >=10 seconds, exit, save complete emulator log.
