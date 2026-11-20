# PC factory raw owner collision policy (2026-11-21)

Parent 13249b458ca4bc9c5f3f5a327791b6c87822b497; code 8292c004bffc5bedc44f34aad5672552c3941fc3. Status PENDING_HEAD_CI, offline editor only.

Primary references: https://github.com/TheLeonX/NSC-ModManager/releases (v2.1.2.1 release 502c38d, upstream main 276116e); https://github.com/TheLeonX/NSC-Toolbox/releases (v2.1.2.1 789fe96); https://github.com/morluto/rea (generic RE tooling). PC Switch Projectiles Target and Start/Stop Deflect do not establish ARM64 Switch ABI. Pinned original main SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9 not independently rehashed.

Existing PC specialCondParam records: 32 bytes, name bytes 0..23, owner u16 little endian at 24..25. Existing NSC_FACTORY_V1 profile format and 1024-capacity seal unchanged. Falsifiable hypothesis: distinct PC owners remapped to one final Switch owner should be rejected in strict composition; last-wins preserved by default. Tests cover disjoint, within/across-file duplicates, explicit remap collision, malformed data and CLI no output on reject. No native hooks or original CPK changes.

Previous HEAD Foundation 44828270273/job 136606336221 and factory 44828270332/job 136606337206 completed success, authentic logs inspected. Current HEAD push CI pending. Sakura aura107, marked/unmarked Event236, and full_moddingapi=false, ready_for_gameplay_test=false, emulator_tested=false preserved.
