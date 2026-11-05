# PC NSC source pack for native ARM64 readers (not an installable Switch mod)

The PC source importer, nine Python raw family decoders, and nine compiled AArch64 raw readers now share a deterministic binary input contract.

**Proven execution:** GitHub Actions 42065894664, completed SUCCESS (67 steps), original job 127379739873 log markers `PC_NSC_NATIVE_PACK_HOST_PASS 24 26 NO_GAMEPLAY` and `PC_NSC_NATIVE_PACK_AARCH64_PASS 22 12 NOT_NATIVE_ENGINE_OR_UZUY`. Tests used authentic pinned PC source template bytes inside a generated fixture ZIP, not an actual user's PC mod or in-game consumer.

This is NOT an installable Atmosphere mod. The original main is not patched. No CRI archive, model/effect/sound/SFX/Japanese voice or actor consumer is connected.

## Prepare on Android / Termux

Stage a real PC ZIP mod first (supports authentic ZIP-format `.nsc`, `.unse`, `.uns`, `.ensc`; special `.nus4` format is not handled):

```sh
cd /storage/emulated/0/Download/switchmain
sha256sum '/storage/emulated/0/Download/MyMod.nsc'
python tools/stage_pc_nsc_mod.py --archive '/storage/emulated/0/Download/MyMod.nsc' --sha256 '<copy exact sha256sum value>' --output '/storage/emulated/0/Download/MYMOD_PC_STAGE'
```

Inspect `MYMOD_PC_STAGE/manifest.json`. Map **only explicitly known raw parameter payloads** to one of the following family identifiers: `susanooCondParam`, `partnerSlotParam`, `ougiAwakeningParam`, `gudoBallParam`, `charRelationParam`, `pairSpSkillManagerParam`, `bgmManagerParam`, `specialInteractionManager`, `guardEffectParam`. A `.xfbin` name does NOT prove NUCC/CRI wrapping; the raw source parser must accept the bytes.

Use the following example JSON as a schema only; the example raw source path must be replaced by the actual source path observed in the staging manifest:

```json
{
  "original_main": {
    "path": "/storage/emulated/0/Download/SWITCH/EXTRACTED_GAME/READY_TO_MOD/exefs/main",
    "sha256": "2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9"
  },
  "mods": [
    {
      "mod_id": "mymod",
      "staged_path": "/storage/emulated/0/Download/MYMOD_PC_STAGE",
      "original_archive": "/storage/emulated/0/Download/MyMod.nsc",
      "source_sha256": "<the exact original ZIP SHA256>",
      "resources": [
        {
          "family": "guardEffectParam",
          "source_path": "PC/param/guardEffectParam.raw.bin"
        }
      ]
    }
  ]
}
```

Save as `/storage/emulated/0/Download/pc_pack_spec.json`, then run:

```sh
python tools/assemble_pc_nsc_param_pack.py --spec '/storage/emulated/0/Download/pc_pack_spec.json' --output '/storage/emulated/0/Download/MYMOD_PC_NATIVE_PACK'
```

The new output directory contains `pc_native_sources.pack` and `manifest.json`. Its bytes are only a caller-owned buffer for `nsc_pc_pack_validate()` and `nsc_pc_pack_row_at()`, reachable via versioned `nsc_pc_pack_get_api()`. Do not deploy it as a game mod.

Format: 64-byte header `NSC_PC_PACK_V1`, version 1, 9 family slots, total length and presence mask, SHA256 of bytes 0..31 plus bytes 64..end; nine 48-byte entries with offset/length, source SHA256, declared record count, zero reserved; canonical 16-byte aligned payloads. Absent slot = all zeros, duplicates are rejected. Native verification checks both the pack and every raw family against existing AArch64 PC source layout reader.

Next engineering milestone is proving original game engine parameter consumer ABI and correct source buffer ownership, so this pack can be used safely. These components do not prove CRC/cpk archive precedence, fileload async ownership, model/effect/audio/Japanese voice, 53 factories or actual Uzuy gameplay.
