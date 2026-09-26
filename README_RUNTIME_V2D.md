# NSC2Switch Runtime V2D — Original Main / Runtime Patch Proof

V2D continues directly from the hardware-PASS V2C lineage.

## Milestone

The deployed `main` is now the untouched v1.70 restore/original NSO:

`2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

The old P128 paired main is kept in this source package only as a verifier reference. It is **not** copied to the runtime artifact.

After the V2 resolver succeeds, `InstallOriginalMainRuntimePatches()` validates the complete patch plan against the original code and recreates the exact proven paired-main text delta in runtime memory using exlaunch `RandomAccessPatcher`.

No write occurs until every required site has resolved uniquely and all 30 original instruction fingerprints match.

## Exact runtime main delta

- 5 condition-count words (512 -> generated total 517)
- 1 P67 source-parity prerequisite (`STR S0,[SP,#0x1C] -> NOP`)
- 24 P128 UJ corridor words:
  - precise gate branch
  - actor reject bypass
  - peer reject bypass
  - type9 success path
  - 19-word precise gate cave
  - lookup success/null path

Total: **30 instruction words**, exactly matching the text-word diff between original v1.70 main and the proven P128 reference main.

## Dynamic discovery

Existing V2C anchors remain resolver-only. V2D additionally:

- finds the five condition patch sites by unique native instruction signatures;
- finds the P67 prerequisite by a unique native instruction signature;
- derives `UJ_SESSION_POST` from the resolved `UJ_SESSION_OUTER` BL callsite;
- finds the native UJ gate locally near that derived post-call site;
- installs the P124 gate hook at the derived gate address, with no gate-offset fallback.

This is the **original-main proof**, not the final no-hardcode release: several older P50/P67/P81 compatibility hooks elsewhere in the lineage still use v1.70 offsets and will be migrated in later V2 stages.

## Expected boot markers

```text
[NSC:V2D] RESOLVER_READY resolved=7 total=7 ... original_main=1 ...
[NSC:V2D] RUNTIME_PATCH_READY words=30 condition_words=5 p67_words=1 p128_words=24 original_main=1 paired_main_file=0 ...
[NSC:V2D] HOOK name=CPK_BIND source=resolver ... installed=1
[NSC:V2D] HOOK name=CHARACODE_GETTER source=resolver ... installed=1
[NSC:V2D] HOOK name=EVENT236 source=resolver ... installed=1
[NSC:V2D] HOOK name=PLAY_ACTION source=resolver ... installed=1
[NSC:V2D] HOOK name=CENTRAL_SETTER source=resolver ... installed=1
[NSC:V2D] HOOK name=UJ_GATE_LOAD source=resolver_derived ... installed=1
[NSC:V2D] HOOK name=UJ_SESSION_POST source=resolver_derived ... installed=1
[NSC:P128A] READY ... runtime_precise_gate_cave=1 original_main_file=1 ...
```

## Test order

1. Confirm artifact `atmosphere/.../exefs/main` SHA-256 is the original-main hash above.
2. Boot to character select and hover/select Tobi.
3. Naruto own UJ.
4. Tobi as victim of enemy UJ.
5. Tobi own UJ through cinematic and return to control.
6. Send the full log + compiled artifact.

Do not mix V2D with an old patched `main`.
