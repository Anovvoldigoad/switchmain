# Public PC raw stream samples

Source repository: TheLeonX/NSC-ModManager at commit
`276116ebf5ba398a867793cb02ee6c33c0927645`.
All samples are exact matching source Git blobs; test verifies each byte,
SHA256, and format inferred from a separate pinned source revision
of TheLeonX/UltimateStormAPI at `a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`.

- Ougi: `ModdingAPIFiles/moddingapi/param/NSC/ougiAwakeningParam.xfbin`, Git blob `091143ccde86ef2a8ecd0c33aa3485726f67f7ab`, 4 bytes.
- Gudo: `ModdingAPIFiles/moddingapi/param/NSC/gudoBallParam.xfbin`, Git blob `934435c5a1e58a1040d62976ff32affd6383e239`, 8 bytes.
- CharRelation: `ModdingAPIFiles/moddingapi/param/NSC/charRelationParam.xfbin`, Git blob `6e680f5c919af3536cc38f8b14fe8138a601770f`, 548 bytes.

These names end with `.xfbin` but the PC API parses their *raw payload*
as uint32 arrays / count-prefixed ID records. They are not NUCC containers.
They are NOT Switch stock assets and do not prove an ARM64 native hook.
