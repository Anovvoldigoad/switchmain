# NSC2Switch ModdingAPI Refactor — Phase 1 Report

## Status

Phase 1 changes are source-verified against the existing R181 verification fixtures.
`NSC_RUNTIME_R181_SOURCE_VERIFY=PASS`.

## What changed

### 1. Stop shipping/replacing the game `main`
The GitHub Actions package now contains only the runtime bootstrap under:

`runtime/atmosphere/contents/0100FA10190A0000/exefs/subsdk9`

No `exefs/main` override is emitted. The original and P128 `main` binaries remain
verification fixtures in the source tree only.

### 2. Bootstrap/core split
Runtime initialization moved from the exlaunch entrypoint into:

- `nsc_runtime_core.hpp`
- `nsc_runtime_core.cpp`

Stable entrypoint:

`extern "C" bool nsc_runtime_initialize();`

`main.cpp` is now only an exlaunch adapter. A future bootstrap can call the same
runtime ABI without moving the gameplay initialization sequence again.

### 3. Generic ModdingAPI CPK path
The CPK bridge now prefers:

`sim:data/moddingapi/NSC2Switch_ModPack.cpk`

and falls back to the legacy:

`sim:data/moddingapi/Tobi_Switch.cpk`

This makes the runtime independent of a specific character CPK name. New
character sets should be compiled/merged into the stable ModPack CPK.

### 4. More runtime resolution, less v1.70 absolute addressing
- R172 SetAnmDirect validation now obtains `CentralSetter` from RuntimeResolver.
- R181 D-pad eligibility gate is now located by a unique eight-word native
  signature instead of `main+0x59CEB4`.
- Both remain fail-closed.

## Important architecture conclusion

`subsdk9` is still the current executable transport, not a gameplay dependency.
With Atmosphere/exlaunch, executable code must enter the process through some
bootstrap. Removing `subsdk9` without replacing that bootstrap means the runtime
will not execute. The useful decoupling is:

- content mods do not contain `main`;
- content mods do not contain `subsdk9`;
- the NSC2Switch runtime bootstrap is installed once;
- the core exposes a stable loader-neutral initialization ABI;
- later the bootstrap transport can be replaced without rewriting core init.

## Remaining high-priority version-coupled hotspots

Do not mass-convert every historical offset. Migrate live paths first.

1. **P81 Ougi/Awakening policy parent** — still fingerprints/installs at a fixed
   v1.70 offset.
2. **P89 actor predicate** — still installs from `kP89ActorPred`.
3. **P125 cleanup request** — still uses the fixed cleanup instruction location.
   P128 post-outer itself is already resolver-derived.
4. **V2N Stage registry lookup** — still fixed. The obvious instruction sequence
   has a duplicate in v1.70, so a plain global unique scan is unsafe; resolve it
   from a parent/caller/global relationship instead.
5. **Event236 helper calls and stage helpers** — several paths still call native
   functions/globals through v1.70 constants even where equivalent resolver
   anchors already exist or can be derived.
6. **Legacy diagnostic/probe constants** — many absolute offsets remain in the
   monolithic bridge file but are not installed by the R181 runtime entrypoint.
   They should be moved to an archived diagnostics module rather than migrated
   blindly.

## Recommended Phase 2 order

1. Add resolver anchors/derived resolvers for P81 and P89.
2. Derive P125 cleanup from the already-resolved UJ/session corridor.
3. Replace remaining direct calls to known anchors (PlayAction, CentralSetter,
   Event236, etc.) with resolver accessors.
4. Build a contextual StageRegistry resolver rather than using the duplicated
   raw signature.
5. Split `nsc_cpk_bridge.cpp` into runtime managers and legacy diagnostics.
6. After core hooks are resolver-only, replace the exlaunch bootstrap transport
   if desired. Content mods already remain unaffected by this step.

## Validation performed

- `bash -n prepare_exlaunch.sh`
- `python3 -m py_compile verify_runtime_r181.py`
- full `python3 verify_runtime_r181.py`
- result: `NSC_RUNTIME_R181_SOURCE_VERIFY=PASS`

Hardware validation is still required before treating the modified runtime binary
as a new hardware baseline, because source verification cannot prove trampoline,
loader, or in-game behavior on Switch hardware.
