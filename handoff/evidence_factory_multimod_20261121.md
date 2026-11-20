# Offline factory profile multi-mod merge — 2026-11-21

Primary sources: [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1) (2026-08-30, Switch Projectiles Target), [NSC-Toolbox 6f780cb](https://github.com/TheLeonX/NSC-Toolbox/commit/6f780cb6814f07e03c16b3e78d97dde4e4368983), [REA f454348](https://github.com/morluto/rea/commit/f45434828103d16cb2b82e6e6373c15d19da9296). None establish a Switch engine consumer ABI.

New slice: compose separately compiled, SHA256-pinned 4160-byte NSC_FACTORY_V1 selector profiles into one deterministic 1024-owner profile with explicit last-wins or reject-collision policy. Decode checks existing profile SHA, canonical order, supported selectors and zero tail; re-encode ensures canonical output. Regression covers collision, source order, corruption, empty/full capacity, and CLI exclusive publication. This is offline class-selector data, not PC runtime semantics or 53 unverified factories.

Original main pinned SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 is not modified. Sakura aura107 and Event236 marked/unmarked unchanged. No native consumer, ownership, callback, lock, async, archive precedence or Uzuy proof. All three release flags remain false.
