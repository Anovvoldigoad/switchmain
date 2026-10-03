# R204G Native mtob + 1nrt Child Trace

R204G is a read-only diagnostic runtime derived from R204F.

R215A proved the internal `mtobprm_load` chunk identity fix: the native low-level lookup now returns non-null. R204F, however, intentionally filtered interesting paths to `mtob`/fixture names and therefore could not show R215A's deliberately pinned native `1nrt...` child resources.

R204G changes only trace visibility:
- preserves all R204F loader/completion/resource/chunk hooks;
- adds `1nrt` path and chunk-key visibility;
- no CPK bind; no path rewrite; no return override; no ID/gameplay patch.

Test with the exact R215A RomFS carrier. Do not change data between R215A and R204G.

Key questions:
1. After `mtobprm_load` internal chunk resolves non-null, do `1nrt...` child LOAD_REQ/FILE_OPEN/SUCCESS_SET events appear?
2. Does `mtobcharsel` later receive RESOURCE_LOOKUP/CHUNK_LOW?
3. Does any `1nrtbod1*` child fail status/read/chunk resolution?
