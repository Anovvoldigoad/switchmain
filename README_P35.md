# P35 — Audit loaded Tobi carrier against stock CPK (read-only)

This is a **diagnostic follow-up to P34**, not a playable mod.

## Ground truth from the prior Android/Uzuy session

An actual P34 log was supplied with `romfs.zip` containing `romfs/data/moddingapi/Tobi_Switch.cpk`.
The run shows `CPK_BIND result=1` for that carrier, **46/46 FILE_OPEN result=1**
and 46 `PROCESS_END status=1 readerr=0`. Across observed P32 LOAD_STATUS lines,
43 had status 2, four had status 0, and none had status 5.
`mtobbod1acc` and `mtobbod1_col3` reached status 2; a
`CHUNK mtobbod1acc` returned a non-null pointer.

This is evidence that the former missing-file/read-error branch was not reproduced.
It **does not** prove model, character actor, enemy, animation or render readiness.
The user still reports visible glitches and enemy disappearance during battle.

The submitted carrier CPK header and TOC show:
- 93 distinct paths (`Sorted=0`, `Align=512`);
- all 72 resources listed in the historical V4 inventory;
- 21 additional global/parameter/UI paths;
- no `mtobskl3.xfbin` path; absence does not prove it was requested.

Of the 21 additional paths, 13 are the V14 parameter-table set (not
proven equivalent to the actual submitted carrier), and eight require
individual comparison to stock:

- `data/message/SWITCH/eng/messageInfo.bin.xfbin`
- `data/message/SWITCH/idid/messageInfo.bin.xfbin`
- `data/message/SWITCH/thth/messageInfo.bin.xfbin`
- `data/sound/cmnparam.xfbin`
- `data/spc/conditionprm.bin.xfbin`
- `data/spc/damageprm.bin.xfbin`
- `data/spc/privateCamera.bin.xfbin`
- `data/ui/flash/OTHER/charicon_s/charicon_s.gfx`

The historical V14 build excluded PC condition/damage/private-camera table
merges as incompatible/unverified. This is **grounds for caution**, not
proof that the eight carrier payloads are corrupted or the cause of invisible enemies.

## Auditor v2 (FastCPK-authoritative, read-only)

This version fixes two high-risk problems in the first P35 draft:

- Uses the same tested \`fastcpk --list\` interface as the previous V3/V4
  investigation, including its absolute per-entry offsets. It no longer
  guesses how CRI @UTF/Cpk FileOffset is based.
- The V4 routing JSON is a **partial** resource list despite
  \`resource_count=72\`; it cannot prove 72/72 paths without a full path
  inventory. Reports now state \`partial_v4_inventory\` explicitly.

Run with Termux (existing FastCPK executable):

\`\`\`sh
python3 audit_p35_carrier.py \
  --stock-romfs /storage/emulated/0/Download/SWITCH/EXTRACTED_GAME/READY_TO_MOD/romfs \
  --carrier /storage/emulated/0/Download/romfs/data/moddingapi/Tobi_Switch.cpk \
  --resource-inventory /storage/emulated/0/Download/TOBI_MTOB_V4_RESOURCE_ROUTING.json \
  --output /storage/emulated/0/Download/P35_CARRIER_AUDIT_V2.json
\`\`\`

The location of the carrier is an example based on the uploaded romfs.zip;
use the actual extracted file location. The stock RomFS option scans all
stock CPK files and detects collisions in \`data/sim/data2.cpk\` as well
as patch/170. A partial check (only patch 170) is possible via:

\`\`\`sh
python3 audit_p35_carrier.py \
  --stock /storage/emulated/0/Download/SWITCH/EXTRACTED_GAME/READY_TO_MOD/romfs/data/patch/170/common.cpk \
  --carrier /storage/emulated/0/Download/romfs/data/moddingapi/Tobi_Switch.cpk
\`\`\`

The tool refuses duplicate CPK names/IDs, out-of-bounds entry offsets,
truncated listings, missing FastCPK, or an incomplete stock listing. It
does not extract, unpack, decrypt, edit, mount, or install any CPK. Packed
payload SHA-256 is not the same as decoded resource SHA-256. The JSON
report is created exclusively (no overwrite).

For reproducibility, the earlier stock patch/170/common.cpk reference
SHA-256 was:
\`a4fb86d7d18b7e85e59e4422808e0e581585da70605228d2cd23da317c1dff27\`.
The audit does **not yet** independently verify that the selected stock
archives match the historical source hashes. Do not claim definitive stock
provenance from the tool alone.

## Interpretation

1. If the eight unverified global files differ from stock, isolate each
   override by content/category and compare formats before proposing a safe
   minimal carrier; do not blindly strip records used by custom actions.
2. If they are byte-identical to stock, they may still affect binder priority
   but do not constitute changed payloads. Focus on actor/model/material/pose
   and child resource references after status=2.
3. `HW.Memory Unmapped Device ReadBlock` events appear later in the captured
   Uzuy log (~108 seconds); they are not on their own proof of either a GPU-driver
   fault or Tobi's exact visual failure cause.

## Update-stability limitation

The visible `CPK_BIND sim:data/moddingapi/Tobi_Switch.cpk` was performed with
an existing native `subsdk9` bridge in P34. Its success does not establish
that placing an arbitrary additional CPK in RomFS without any executable hook
will mount it. Achieving the user's requested update-resilient, ROMFS-only
deployment remains a separate, unsolved engine routing constraint.

Validation: `python3 -m unittest -v test_audit_p35.py`.
