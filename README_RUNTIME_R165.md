NSC2Switch Runtime R165 — Event150 / Voice Read-Only Provenance Probe
Date: 2026-09-28
Target: NSC Switch v1.70 / Build ID 48ece454b61412b9fb46fab2be3f5ef7b2804f39

PURPOSE
- Stage R164 is hardware PASS and is frozen.
- Trace UltimateStormAPI custom Event150 named voice cues without changing gameplay/audio.
- Compare those events with the game's genuine native ME_VOICE path.

STATIC PROOF
- Tobi PRM serializes mtob_ougi_001/002/003 with event type 0x96 (150).
- Known event121 anchor main+0x8134F8 plus native 0x30 registration stride resolves event150 to main+0x813ECC.
- The registration name associated with that callback is ME_SET_CAPTION: Event150 is a PC API repurpose, not a native named-voice callback.
- Native ME_VOICE is main+0x813D88 and performs command=(int16(event+0x24)+0x7000), then actor vtable+0x1030.

R165 HOOKS
1. main+0x813ECC Event150: logs cue text and fields, calls Orig unchanged, logs return.
2. main+0x813D88 ME_VOICE: logs native voice index/command, calls Orig unchanged, logs return.

NO MUTATION
- no voice playback injection
- no Character Sound Entry/ACB mutation
- no stage change
- no P128 change
- no D-pad change
- no opcode26 change
- original main remains exact v1.70

TEST
Keep R164 Tobi_Switch.cpk. Build/install only R165 subsdk9 + original main, fresh boot, enter battle as Tobi, trigger normal attacks/skills, win if practical, and one UJ. Send full Uzuy log.

DECISION
A. EVT150 cue=mtob_ougi_* appears, no corresponding native ME_VOICE: missing Event150 compatibility dispatcher proven.
B. EVT150 appears and native ME_VOICE appears: inspect command and Character Sound Entry/ACB resolution.
C. No EVT150 during source-authored UJ: event dispatch/PRM ingestion boundary is upstream and must be traced.
