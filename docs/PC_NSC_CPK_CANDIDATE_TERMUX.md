# Termux: Source-pinned PC NSC CPK candidate build (NOT a gameplay release)

This stage prepares byte-identical PC CPK files and a binary registration profile for the existing Switch v1.70 moddingapi experiment. It does **not** rebuild CRI archives, port XFBIN commands, attach live CRI archive handlers, identify the true archive winner, or install an Atmosphere mod. It refuses any overlapping CPK TOC path because native precedence remains unproved.

1. Stage each authentic PC ZIP mod (extensions .nsc/.uns/.unse/.ensc only):

```sh
cd /storage/emulated/0/Download/switchmain
sha256sum '/storage/emulated/0/Download/Example.nsc'
python tools/stage_pc_nsc_mod.py --archive '/storage/emulated/0/Download/Example.nsc' --sha256 '<the exact 64-digit SHA256 from sha256sum>' --output '/storage/emulated/0/Download/EXAMPLE_PC_STAGE'
```

2. Check EXAMPLE_PC_STAGE/manifest.json for actual CPK filenames. Do not guess whether a PC mod contains a CPK or its resource path. Use the exact paths from that manifest.

3. Write a source-pinned JSON specification. This is a **shape example**, not a claim these example files or PC paths exist in your mod:

```json
{
  "original_main": {
    "path": "/storage/emulated/0/Download/SWITCH/EXTRACTED_GAME/READY_TO_MOD/exefs/main",
    "sha256": "2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9"
  },
  "mods": [
    {
      "mod_id": "example",
      "staged_path": "/storage/emulated/0/Download/EXAMPLE_PC_STAGE",
      "original_archive": "/storage/emulated/0/Download/Example.nsc",
      "source_sha256": "<real archive sha256>",
      "cpks": [
        {
          "source_path": "Resources/CPKs/example.cpk",
          "runtime_path": "sim:data/moddingapi/example/example.cpk",
          "priority": 10
        }
      ]
    }
  ],
  "reference_archives": []
}
```

Only replace example paths and hashes with actual observed values. `reference_archives` optionally accepts read-only SHA-verified `{"label":"source1","path":"/path/to/source.cpk","sha256":"..."}` records for conservative TOC conflict checks; supplying these bytes does **not** authenticate their historical stock provenance.

4. Generate candidate staging in a new, nonexistent folder:

```sh
python tools/assemble_pc_nsc_cpk_candidates.py --spec '/storage/emulated/0/Download/example_spec.json' --output '/storage/emulated/0/Download/EXAMPLE_CPK_CANDIDATE'
```

The output consists of `candidate_cpk_registration_profile.bin`, `candidate_manifest.json`, and `candidate_data_root/data/moddingapi/` with original CPK bytes. They are **not** an installable mod; do not place them in a live game or blindly rename the profile as a valid subsdk/main patch.

The program refuses unsupported malformed CPK UTF/CRC/TOC metadata, case-insensitive duplicate TOC paths, corrupt source/CPK hashes, symlinked staged CPKs, duplicate registration priorities, and existing output folders. All real CRI registration, asynchronous completion, lock/unlock, unbind, destructor and resource compatibility semantics still require concrete original native ABI proof and Uzuy testing.
