# R276H19B — Minimal external-CPK binder reconstruction

Purpose: isolate archive-provider/mount semantics after R276H18A proved that a 97-file historical-content union still fails at VS when exposed through `data/patch/170/sound.cpk`.

This is a reconstruction of the proven P6/P13-E mount contract, **not a claim of byte identity with historical `adb122...`**.

## Runtime scope

Exactly one trampoline is installed:

- `main+0x473190` — native CPK bind-with-priority boundary.

Behavior:

1. Call `Orig()` for the game's vanilla CPK bind.
2. On the first successful `sim:` bind only, call the same native function again with:
   - path `sim:data/moddingapi/Tobi_Switch.cpk`
   - priority `32`
   - remaining descriptor fields zero (historical plaintext/encryption=0 contract)
3. Never alter the original return value.
4. Fail closed unless the exact v1.70 eight-word fingerprint at `main+0x473190` matches.

No characode, resource-loader, stage, event, Ougi, visibility, action, or gameplay hook is installed.

## Deterministic build environment

- `devkitpro/devkita64:latest`
- exlaunch pinned to `229bbd6`
- `LOAD_KIND := Module`
- `PROGRAM_ID := 0100FA10190A0000`
- `CXX_FLAGS := -Wno-non-c-typedef-for-linkage`

Historical exact P13-E binary target, for provenance only:

- size `61878`
- SHA256 `adb1222067af11d987e85880116cc4c00b8297ca82c84a93fa9f7370ac641056`

A rebuilt H19B binary is expected to be semantically equivalent in the mount axis but is **not required or expected to reproduce that historical hash** because the original P6 source ZIP is no longer available.

## Build

Push this directory to a GitHub repository and run the Actions workflow:
`.github/workflows/build-minimal-binder.yml`.

Download artifact `NSC-R276H19B-minimal-binder` and report:

- `SUBSDK9_SIZE`
- `SUBSDK9_SHA256`
- full build log if compilation fails.

Do not deploy until static audit of the produced NSO is complete.


## R276H19C CI PATH fix
The current devkitPro devkita64 image does not guarantee devkitA64/bin is on PATH for GitHub Actions shell steps. The build step now explicitly sets DEVKITPRO=/opt/devkitpro, DEVKITA64=/opt/devkitpro/devkitA64, prepends both tool directories to PATH, and fails closed if aarch64-none-elf-g++ is absent. No runtime source or hook semantics changed.
