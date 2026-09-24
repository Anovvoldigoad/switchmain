# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R99

## P97A v2 compile-order hotfix

P97A v1 failed at C++ compile time before link/runtime:
- `InstallP97Internal()` referenced `MatchWords()` and `LogFingerprintFail()` before either was declared.
- GCC errors were at the P97 installer only; this was not a hook/trampoline/runtime failure.

### Fix
Added forward declarations before the P97A block:

```cpp
template <size_t N>
bool MatchWords(ptrdiff_t offset, const uint32_t (&expected)[N]);
void LogFingerprintFail(const char* name, ptrdiff_t offset);
```

Shared definitions remain unchanged later in the translation unit.

### Semantics unchanged
No change to:
- hook target `main+0x7EFEBC`;
- fingerprint words;
- semantic-UJ gate;
- data-driven ougiAwakening membership gate;
- current action707 gate;
- descriptor707 key test;
- `E94=136`, `E9C=0`, `BDA4=1`, `BDA8=0`, `BDC8=0` pre-handoff gate;
- guarded native no-transition return `0`;
- fallback `Orig(actor, context_code)`;
- paired main / restore main.

No char281 gameplay branch, no force708, no force710, no action rewrite.

### Verification
`verify_p97a_source.py` now checks compile-order declarations are visible before `InstallP97Internal()`.
Minimal GCC compile test of the same forward-declaration/late-definition pattern: PASS.

### Immediate next action
Build `build-subsdk9-p97a.yml` from the P97A v2 source kit. If compilation advances beyond `nsc_cpk_bridge.cpp`, preserve the complete next build/link output. If artifact builds, audit hashes/markers then run vanilla UJ + custom UJ.
