# R204K native charsel generic-child lifecycle trace

R204K keeps the R204J registry/tree probes read-only and adds full loader visibility for the prefixless generic body-child family (`data/spc/bod1*`).

Why: R221A changed the exact blocker `data/spc/bod1_col2.xfbin` from final failure status 5 to pending status 1, proving the alias affected resolution, but R204J filtered that generic path from LOAD_CREATE/REQ, FILE_OPEN, PROCESS, completion writers, RESOURCE_LOOKUP, and CHUNK_LOW.

New visibility:
- `data/spc/bod1*.xfbin` participates in all existing loader/completion/resource-consumer probes.
- `bod1*` internal chunk keys participate in CHUNK_LOW logging.
- Existing `OWNER_TREE_VERIFY`, `REGISTRY_PROCESS`, and `TARGET_REGISTRY_OWNER_READY` probes remain unchanged.

No arguments, return values, paths, hashes, registry nodes, load states, or gameplay state are modified. Keep the R221A sound.cpk unchanged for this test.

Hardware protocol: cold boot, hover one working vanilla preview briefly, then the target slot for 10+ seconds, exit, and provide the full log plus visual result.
