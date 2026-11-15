# PC raw ModdingAPI readers inside the Switch ARM64 module — scope

The existing Python nine-family readers have been ported to bounded AArch64 C++ in `overlay/source/program/nsc_pc_raw.cpp`. This is a *runtime-compiled source-data reader*, not a Switch native game parameter hook. The original v1.70 main is untouched. The table is reachable through `nsc_pc_raw_get_api()` (API version 1, nine families).

| Family ID | Source format | Source fields exposed |
|---|---|---|
| 0 | susanooCondParam, raw 0x20 | type checked against public PC set; u16 ID at +0x18 |
| 1 | partnerSlotParam, raw 0x20 | type checked; u16 ID at +0x18 |
| 2 | ougiAwakeningParam, LE u32 stream | ordered ID |
| 3 | gudoBallParam, LE u32 stream | ordered ID |
| 4 | charRelationParam, u32-length-prefixed arrays | count and byte extent |
| 5 | pairSpSkillManagerParam, 0x18 rows | signed raw fields as u32 bits at +0x10/+0x14; optional one ignored terminal byte |
| 6 | bgmManagerParam, 0x68 rows | raw fields at +0x60/+0x64 |
| 7 | specialInteractionManager, variable count + ID/trigger arrays | main ID and raw trigger count |
| 8 | guardEffectParam, 0xF8 rows | two raw u32 fields at +0x00/+0x04 |

Native C ABI:
```cpp
const NSCPcRawAPI* api = nsc_pc_raw_get_api(); // version=1, family_count=9
NSCPcRawSummary summary{};
if (api && api->validate(8, bytes, size, trusted_sha256_bytes, &summary)) {
    NSCPcRawRow row{};
    const bool ok = api->row_at(8, bytes, size, trusted_sha256_bytes, 0, &row);
    // row.offset and row.length index ORIGINAL CALLER-OWNED bytes only.
    // Do not expose row into game engine until object/ownership ABI is proven.
}
```

The caller must keep input bytes alive. No memory ownership, allocation, CRI file binding, game actor, model/effect/audio/Japanese voice, or engine consumer is implemented by these readers. The game does not yet call these readers from its native parameter loading flow.

Tests:
- `python tests/test_native_pc_raw_nine.py --output NEW_OUTPUT` runs a host C++ implementation and compares all nine authentic pinned PC source fixtures with Python reader parity and invalid inputs. Needs gcc, g++ and Python.
- `python tests/test_native_pc_raw_arm64.py --main ORIGINAL_MAIN --elf COMPILED_RUNTIME_ELF --output NEW_OUTPUT` executes the AArch64 functions via Unicorn against the same nine fixtures. It checks the exact main SHA and tests no-write-on-validation-failure. Requires the GitHub Actions-generated ELF and dependencies, not an Android game runtime.
- Verified CI 42057187119, full 65 steps SUCCESS, log job 127348672877. ARM64 calls 30 positive/19 negative; host row views 123 matching/39 negative.

No switch gameplay claims; three release flags remain false.
