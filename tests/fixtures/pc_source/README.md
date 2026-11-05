# Public NSC-ModManager PC parameter format fixtures

These two small source files are exact Git blobs from the public
TheLeonX/NSC-ModManager repository, pinned commit
276116ebf5ba398a867793cb02ee6c33c0927645.

| Local fixture | Upstream raw file | Git blob |
| --- | --- | --- |
| NSC_susanooCondParam.raw32.bin | ModdingAPIFiles/moddingapi/param/NSC/susanooCondParam.xfbin | d983860d4bbaa58440ea1b3ba2b6e6e33fa48b17 |
| NSC_partnerSlotParam.raw32.bin | ModdingAPIFiles/moddingapi/param/NSC/partnerSlotParam.xfbin | 8155d1e0a76add995051b45fe68d27f19cca49dc |

Upstream .xfbin extension here denotes raw PC ModdingAPI 0x20-byte parameter
records, NOT a NUCC XFBIN container. PC source layout was checked at
TheLeonX/UltimateStormAPI commit a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc.

Git blob identity and file SHA256 are checked from bytes during CI.
Neither template is an authenticated Switch stock game input or PC manager517.
No native Switch actor/factory ABI or gameplay compatibility is established.
