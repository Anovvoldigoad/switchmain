# R264 — Secondary Preview Object + Draw Trace

Use with the exact **R263 sound.cpk**. Replace only `subsdk9`.

Expected decisive markers:
- `[NSC:R264] SECONDARY_FILE_LOOKUP ...`
- `[NSC:R264] SECONDARY_CHUNK_LOOKUP ... key=... result=...`
- `[NSC:R264] SECONDARY_BUILD_POST ... secondary98=...`
- `[NSC:R264] DRAW_PRE ... secondary98=...`
- `[NSC:R264] DRAW_SUBMIT ...`

Interpretation:
- chunk lookup NULL + secondary98 NULL: secondary charsel typed-chunk path is the blocker.
- chunk lookup non-null but secondary98 NULL: constructor/allocation path after lookup is blocker.
- secondary98 non-null but no DRAW_SUBMIT: draw context/gate is blocker.
- DRAW_SUBMIT reached while preview still empty: blocker is downstream renderer/scene data.
