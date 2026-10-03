# NSC2Switch ModdingAPI Architecture — bootstrap/core split

## Goal

Content mods must not ship a patched game `main` and must not each carry their
own runtime bootstrap. The NSC2Switch runtime is installed once; character mods
are RomFS/data packages.

## Phase 1 implemented here

- Game `main` is no longer packaged or overridden.
- `subsdk9` is treated only as the current bootstrap transport.
- Runtime initialization moved behind stable C ABI:
  - `extern "C" bool nsc_runtime_initialize();`
- `main.cpp` is now a thin exlaunch adapter.
- The proven R181 gameplay install order is unchanged.
- Original/P128 `main` files remain local verification fixtures only; they are
  not release payloads.

## Deployment layers

1. **Runtime core — install once**
   - `atmosphere/contents/0100FA10190A0000/exefs/subsdk9`
2. **Content mods — data only**
   - `atmosphere/contents/0100FA10190A0000/romfs/data/moddingapi/*.cpk`
   - any required UI/icon files under their normal RomFS paths

A content-mod release must contain no `exefs/main` and no `exefs/subsdk9`.

## Why `subsdk9` still exists

Horizon/Atmosphere needs executable code to enter the game process somehow.
With the current exlaunch backend that transport is an NSO loaded in a subsdk
slot. Removing the file without replacing the bootstrap would mean the runtime
never executes. The important decoupling is therefore:

- gameplay/runtime core does not own the exlaunch entrypoint;
- content mods do not ship the bootstrap;
- the bootstrap can later be replaced by an external loader that calls
  `nsc_runtime_initialize()`.

## Phase 2 — next refactor

Migrate remaining active v1.70 absolute-offset users into RuntimeResolver
anchors/derived signatures. High-priority active paths include:

- R181 native eligibility fingerprint
- P81/P89/P124/P125 portions reached by P128
- Stage registry lookup proof
- action registry/lookup functions used by generic D-pad work

Fail closed on zero or multiple signature matches. Keep expected v1.70 offsets
only as diagnostics, never as fallback addresses.

## Phase 3 — generic ModdingAPI content loader

The bridge now prefers one stable generic pack path:

- `romfs/data/moddingapi/NSC2Switch_ModPack.cpk`

and falls back to the old `Tobi_Switch.cpk` package for compatibility. The packer
should merge/compile enabled character content into the generic ModPack CPK. This
keeps character additions/removals out of the runtime binary.

A later enhancement may add a runtime manifest or generic CPK slots, but that is
not required to remove per-character runtime rebuilds.
