# R249 — Post-Identity Resource Trace

R248 hardware proved the target model identity is `46` and the native identity-table lookup succeeds, yet `model+0x90` stays null. R249 traces the exact downstream gates in model init: completed file-resource lookup, typed chunk lookup, and the `0x3B0` allocation whose pointer is later stored to `model+0x90`.

Expected artifact: `NSC2Switch-R249-POST-IDENTITY-RESOURCE-TRACE`.

Deployment remains the same single-variable diagnostic setup: clean `main`, same R245C carrier, external ModdingAPI CPK off, ID281 off, replace only `subsdk9`.
