# Last four PC ModdingAPI parameter format templates

These are exact unchanged public *raw PC* parameter samples from
`TheLeonX/NSC-ModManager` commit `276116ebf5ba398a867793cb02ee6c33c0927645`,
stored with their original Git blob identities. The source entrypoints
below were inspected at `TheLeonX/UltimateStormAPI` commit
`a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc`.

| Family | Source format | Upstream source |
|---|---|---|
| pairSpSkillManagerParam | 0x18: char[16], int32, int32 (optional trailing byte on PC) | TeamUltimateJutsuManager.cpp |
| bgmManagerParam | 0x68: char[48] stage, char[48] sound, int32 BGM ID, int32 unknown | BGMManager.cpp |
| specialInteractionManager | int32 total entries then int32 main, int32 trigger count, int32[count] | SpecialInteractionManager.cpp |
| guardEffectParam | 0xF8: uint32 char, uint32 mode, five char[48] | GuardEffectParam.cpp |

Input SHA256s and Git blobs are checked from actual bytes in tests.
Source format is PC-specific; the file extension `.xfbin` does NOT mean
these raw payloads are NUCC containers. This component does not include
a Switch native loader, CRI archive lifecycle, effects, audio, CRC32
binding, actor lifecycle, or proven gameplay. No game archives are stored.
