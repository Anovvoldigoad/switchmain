# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R104

## Baseline
- Game: Naruto x Boruto Ultimate Ninja Storm Connections — Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin: `229bbd6`

## Locked rules
- Generic/data-driven only; char281 remains a diagnostic fixture, never a gameplay branch.
- Preserve P50 victim-safe Event236 shadow and P89 actor-predicate admission bridge.
- Correct custom UJ graph is user-confirmed: `700 -> 707 -> 708 -> 710 -> cinematic`.
- Do not suppress 708. Do not force 710. Do not write E94/E9C/EA4/BDA4/BDA8/BDC8 speculatively.
- Do not globally patch wrapper `0x772594`.
- No manual BLR replay without ABI proof.

## P99A uploaded artifact audit
Uploaded compiled artifact is structurally consistent with the test run:
- SHA256SUMS internal verification: PASS.
- paired main hash: baseline PASS.
- restore main hash: baseline PASS.
- compiled `subsdk9` SHA256: `a1c1b7df24289b5b8428a708ec8308853d23eea2f95cd1b40b3850c874b11c6e`.
- runtime `[NSC:P99A] READY ... probe=1` is present in log43.

Note: the old source-package `verify_p99a_artifact.py` attempts to find plain marker strings directly inside the compressed NSO and can false-fail `MARKER_MISSING`; runtime READY is the authoritative linked-marker proof for this artifact. The hash/NSO checks themselves pass.

## P99A runtime result — decisive
Test run contains a successful vanilla UJ using char91 and a failing custom char281 UJ.

### Vanilla char91
- `700 -> 707 -> 710`.
- `PlayAction710` succeeds from caller `main+0x7E6EC8`.
- P91 handoff confirms `707 -> 710`.
- dynamic topology at 710:
  - +0x1278 -> `0x7EB518`
  - +0x12C8 -> `0x794E74`
  - +0x12D0 -> `0x794EBC`
  - +0x1988 -> `0x7EB270`
- The attacker char91 does NOT run through P99 `GATE1278` before its successful 710 handoff.

### Custom char281
- `700 -> 707 -> 708` occurs natively.
- topology at 707/708 is the same implementation set as vanilla:
  - +0x1278 -> `0x7EB518`
  - +0x12C8 -> `0x794E74`
  - +0x12D0 -> `0x794EBC`
  - +0x1988 -> `0x7EB270`
- Therefore vtable/class implementation mismatch is eliminated for these slots.
- During action708, `GATE1278` is called twice for the custom attacker and returns 1.
- The second call is from cleanup caller `main+0x7EAF00`; immediately afterward state125 is visible again.
- `SW_MTOB_XH` EVT121 executes immediately before cleanup, but does not itself change action/E94/E9C.
- No PlayAction710 occurs for custom.

## Correct interpretation of P99
P99's cleanup predicate is NOT the primary missing-710 gate.
The successful vanilla attacker reaches 710 without entering that cleanup predicate first.
Custom enters cleanup only after action708 has continued without producing the native 710 handoff.
Thus cleanup/state125/action261 are downstream fallback/termination behavior after the true handoff path failed to materialize.

## Static action710 producer proof
Pinned v1.70 main disassembly:
- `0x7E6EA8`: `MOV W1,#710`
- `0x7E6EC4`: `BL 0x766B8C` (PlayAction route)
- return address / runtime caller: `0x7E6EC8`

Immediate producer corridor:
- `0x7E6C18`: actor setup / vfunc path
- `0x7E6C2C`: prepares participant lookup
- `0x7E6C30`: calls `0x880150`
- `0x7E6C38`: if lookup result is null, branch direct to `0x7E6EA8`
- non-null lookup path maps/remaps 710 through `0x76BDC0`, then converges at `0x7E6EAC`

Earlier branch family:
- `0x7E6A58` safe corridor landmark before branch family
- `0x7E6BB4` identifies the zero-source path
- `0x7E6B08` follows actor vslot +0xC48 on the alternate path and exposes its native return

## P100A — native action710 corridor landmark trace
Functional parent: P96A. P97/P98/P99 installers are not called.

P100A uses five INLINE probes only; zero whole-function trampolines:
1. `0x7E6A58` — `ENTRY_7E6A58`, replaces/reproduces `MOV X26,X23`.
2. `0x7E6BB4` — `ZERO_PATH_7E6BB4`, replaces/reproduces `LDR W8,[X19,#E54]`.
3. `0x7E6B08` — `C48RET_7E6B08`, replaces/reproduces `MOV X22,X24`; logs W0 after vslot+C48.
4. `0x7E6C34` — `LOOKUP_7E6C34`, replaces/reproduces `MOV X22,X24`; logs X0 result of `0x880150` and W21.
5. `0x7E6EA8` — `REQUEST710_7E6EA8`, replaces/reproduces native `MOV W1,#710` exactly.

P100A does NOT replay a BL/BLR, does not force control flow, does not force 710, and does not write actor gameplay state.

Markers:
- `[NSC:P100A] READY`
- `[NSC:P100A] LANDMARK ... stage=...`

## P100A decision matrix
Run one successful vanilla UJ followed by one custom Tobi UJ.

- Vanilla reaches ENTRY + REQUEST710; custom never reaches ENTRY:
  divergence is upstream of `0x7E6A58`; trace caller/entry into the larger UJ controller next.
- Both reach ENTRY, but custom misses both ZERO_PATH/C48RET:
  divergence lies in the short block between `0x7E6A58` and the `0x7E6A94` branch family.
- Custom reaches ZERO_PATH or C48RET but not LOOKUP:
  the branch family before `0x7E6C18/34` is the exact next target.
- Custom reaches LOOKUP but not REQUEST710:
  inspect lookup/remap result and branch at `0x7E6C38` / `0x76BDC0`.
- Custom reaches REQUEST710 but no PlayAction710:
  failure is at/after wrapper `0x766B8C`, which would contradict current P93/P91 observations and becomes immediately testable.

## Runtime test order
1. Boot sanity + `[NSC:P100A] READY ... probe=1`.
2. Successful vanilla UJ through cinematic.
3. Custom Tobi UJ through `707 -> 708` failure.
4. Upload log and compiled P100A artifact.
