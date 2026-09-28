# NSC Runtime R166 — Sound1030 Read-Only Voice Provenance Probe

R166 follows an R165 hardware run where Tobi voice was audible.

R165 proved:
- Event150 named cues `mtob_ougi_001/002/003` and `mtob_win00` execute.
- Tobi voice/SndEvent XFBIN assets load and open successfully.
- No hooked native `ME_VOICE` callback at `main+0x813D88` executed for custom Tobi.
- R165 was read-only, so the audible voice came from another existing audio path.

R166 therefore hooks the hardware-proven concrete actor sound dispatcher at `main+0x635DA0` (actor vtable+0x1030) read-only.

It logs all custom-actor sound commands and correlates them with the most recent Event150 cue. It never injects playback and never changes sound registries, stage state, P128, or D-pad behavior.

Build artifact name:
`NSC-RUNTIME-R166-sound1030-readonly-probe`

For hardware:
1. Keep the working R164 StageInfo-fixed CPK unchanged.
2. Replace runtime with the R166 artifact.
3. Fresh boot.
4. Use Tobi, perform UJ to completion, and trigger ordinary attacks/victory if convenient.
5. Report whether Tobi voice was audible and provide the full Uzuy log.
