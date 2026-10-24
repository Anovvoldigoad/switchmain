# P37 — preserve original Tobi carrier storage

This branch addresses the user's **P36 failed-to-boot** report. It is not a playable mod or a proven fix.

## Critical packaging difference found

The actual Android P36 run reported:

| Attribute | Original Tobi carrier | P36 rebuilt candidate |
| --- | --- | --- |
| Entries | 93 | 93 |
| Files processed by CC2 | 1 | 93 |
| CRILAYLA files | 0 | 81 |
| Stored payload size | 165.91 MiB | 67.03 MiB |
| Alignment | 0x200 | 0x200 |
| Header `Sorted` | 0 (from original P35 report) | FastCPK template pack implementation sets 1 |

The first four values come from the user's recorded FastCPK output.
The `Sorted=1` behavior of rebuilt archives is inferred from
FastCPK source `pack.rs` (the header is built using
`cli.template.is_some()` as the `sorted` flag), rather than from
a submitted P36 header dump. This is a serious incompatibility risk
because the original carrier is marked unsorted.

The user also provided `uzuy_log(22).zip` after P36 failed to boot.
The current analysis environment could not open the ZIP, so no error
lines have been extracted from that log and no crash root cause is asserted.

## P37 method

`build_p37_preserve_carrier.py` uses the **same three stock battle
parameters** as P36. It first fully decodes the source stock and carrier
CPKs, and establishes an exact original decoded hash baseline. It
then rebuilds the 93-entry carrier template with these changes:

- The three battle parameter XFBINs are taken from stock Switch 1.70
  **only when their decoded hashes differ**.
- For **every other entry**, the builder writes the ORIGINAL STORED
  bytes directly from the original Tobi CPK into staging.
- The packer is run with **no new CC2 encryption and no CRILAYLA
  compression**, and with the original `0x200` alignment.
- Since template packing writes `Sorted=1` even for originally
  unsorted carriers, `cpk_p37_compat.py` restores the original
  `Sorted` value in the generated CPK header.
- The output is re-extracted; all 93 decoded payloads, paths and
  numeric IDs are checked. The **90 untouched stored payloads must
  match the original CPK byte-for-byte**, not just after decoding.
- The stock and original carrier SHA-256 values must be unchanged.
  A fully verified candidate is the only file promoted to the output
  folder. Failed builds keep no final candidate.

The input carrier must not contain any CRILAYLA-compressed entry
(`packed_size != extracted_size`), because raw stored copy would
otherwise require preserving each compressed entry's decoded-size
metadata. The actual user P36 extraction reported 0 CRILAYLA files,
but the P37 preflight enforces the condition and aborts rather than
silently re-encoding inputs.

This removes the major **packaging** confound from the P36 failed-boot
experiment. It still does NOT prove that three global files cause the
invisible opponent, that all CPK metadata matches perfectly, or that
P37 boots. A controlled runtime check is still required.

## Termux (existing clone)

```sh
cd ~/P36_TOBI
git fetch origin research/p37-preserve-carrier-encoding
git switch -c research/p37-preserve-carrier-encoding --track origin/research/p37-preserve-carrier-encoding

python3 -m unittest -v test_cpk_p37.py test_build_p36.py

python3 build_p37_preserve_carrier.py \
  --stock /storage/emulated/0/Download/SWITCH/EXTRACTED_GAME/READY_TO_MOD/romfs/data/patch/170/common.cpk \
  --carrier /storage/emulated/0/Download/romfs/data/moddingapi/Tobi_Switch.cpk \
  --output /storage/emulated/0/Download/P37_TOBI_BUILD
```

Use a fresh output folder and keep the **old known-booting**
`Tobi_Switch.cpk` installed. Never install P36 again.

Expected output (if every verification passes):

```text
P37_TOBI_BUILD/
  Tobi_Switch_P37_PRESERVED_ENCODING_UNTESTED.cpk
  P37_BUILD_REPORT.json
```

A successful **offline** report is not permission to label the
mod playable. Treat the candidate as a reversible runtime experiment
and preserve an independent original backup.

## Next decision

- If P37 aborts on input size/format or fails decoded/stored validation:
  do not install anything; inspect the exact error.
- If P37 passes offline verification: check that the result still has
  `Sorted=0`, `Align=512`, the original 90 stored resources and only
  three actual parameter changes.
- If a P37 runtime test still fails to boot, isolate TOC/header
  compatibility (ideally a zero-payload-change identity rebuild)
  before attributing any issue to the three battle globals.
