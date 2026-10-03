# R204I Native Charsel Owner Registration Trace

R204I keeps the full read-only R204H loader/completion/resource/chunk trace and adds the two owner-registration boundaries that R204H missed.

New probes:
- `main+0x116175C` `OWNER_INIT5`: five-argument owner initializer used by the registry path.
- `main+0x1161B88` `OWNER_REGISTER`: path-hash registry lookup/create that calls `0x116175C`, inserts the owner into the tree, and returns the path hash.

Retained probes include `OWNER_READY` (`0x11617CC`), `OWNER_STATE` (`0x1161858`), loader completion, resource lookup, and chunk lookup. R204I is read-only: no path rewrite, return override, CPK bind, gameplay patch, or ID patch.

Hardware protocol: keep the exact R215A `sound.cpk`. Cold boot. Hover one known-working vanilla character for a few seconds, then the target slot for 10+ seconds, then exit. The decisive comparison is whether the working vanilla charsel produces `OWNER_REGISTER/OWNER_INIT5 -> OWNER_READY`, while `mtobcharsel` does not.
