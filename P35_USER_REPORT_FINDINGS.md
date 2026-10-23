# P35 — Findings from user-supplied P35_RESULT.json (24 October 2026)

## Provenance and scope

The user supplied `P35_RESULT.json` after running the older,
single-stock-CPK P35 audit on Android. Its schema has
`overrides_relative_to_this_stock_cpk` rather than the current
multi-CPK `stock_path_collisions` fields. The report contains stored
entry hashes and header information; it **does not** contain decoded
XFBIN comparisons or an original stock CPK SHA-256 provenance check.

This is analysis of the report supplied by the user, **not** a
fresh execution over original game archives. No binary was installed,
patched, or modified.

## Exact findings

| Observation | Value |
| --- | --- |
| Stock reference | `data/patch/170/common.cpk`, 728 entries |
| Custom carrier | `data/moddingapi/Tobi_Switch.cpk`, 93 entries |
| Same-path entries against *this* stock CPK | 19 |
| Stored-byte hash differences among those 19 | 19 |
| Same-path V14-named parameter tables | 13 |
| Same-path unverified global files | 6 |
| Paths outside *this* stock CPK | 74 |
| `mtobskl3` present in carrier | No |
| Stock `Sorted` / `Align` | 1 / 2048 |
| Carrier `Sorted` / `Align` | 0 / 512 |

The 13 parameter-table matches are **classified by filename**; the
audit does not prove their bytes came from the V14 build.

### Six global override candidates (all differ in *stored* bytes)

- `data/message/SWITCH/eng/messageInfo.bin.xfbin` (931,908 → 3,102,348 packed bytes)
- `data/message/SWITCH/idid/messageInfo.bin.xfbin` (875,364 → 3,080,560)
- `data/message/SWITCH/thth/messageInfo.bin.xfbin` (1,237,056 → 5,200,764)
- `data/spc/conditionprm.bin.xfbin` (5,900 → 91,344)
- `data/spc/damageprm.bin.xfbin` (36,688 → 296,188)
- `data/spc/privateCamera.bin.xfbin` (804 → 12,716)

Sizes are stored CPK entry sizes, **not decoded XFBIN sizes**.
Different compression/encryption explains some possible differences;
none of these six has yet been proven to be a malformed XFBIN.

The two other global files outside `patch/170/common.cpk` are
`data/sound/cmnparam.xfbin` and
`data/ui/flash/OTHER/charicon_s/charicon_s.gfx`.
Their presence outside this one CPK is not proof that other
stock CPKs lack them.

The V4 inventory independently identified a source asset,
`data/bossNrt/08/b01cmneff1.xfbin`, in `data/sim/data2.cpk`.
Thus `new_relative_to_this_stock_cpk` must **never** be
interpreted as genuinely new relative to all 28 stock CPKs.

## Relationship to actual Uzuy P34 log

The earlier supplied log showed 46 `FILE_OPEN result=1`,
46 completed native process scopes (status 1/readerr 0 immediately
after processing), 43 separately observed `LOAD_STATUS=2`,
and no `LOAD_STATUS=5` in the captured window.

This narrows the old open/read-failure theory, but does not
establish that every actor/model/material is successfully created,
that the global override payloads are semantically correct, or
that the visual glitches are caused by these six files.

The carrier has `Sorted=0/Align=512` versus stock
`Sorted=1/Align=2048`. This metadata difference warrants a
controlled compatibility check, **not** an unreviewed patch:
the recorded successful opens mean it cannot simply be declared
the root cause.

## Decision and next controlled comparison

1. Do **not** remove/replace the six globals from a playable build
   without checking their decoded contents and whether custom
   `mtob` uses any of their records.
2. Confirm source provenance and compare decoded
   `conditionprm`, `damageprm`, and `privateCamera` first;
   prioritize them because they are battle-global and V14 treated
   the corresponding PC merges as unverified, **not** because this
   report proves they caused the invisible opponent.
3. Compare the three messageInfo files and the 13 identified
   parameter tables separately; investigate `cmnparam` and UI gfx
   using a full 28-CPK inventory.
4. Use existing P35 v3 `--decoded-root` + V4 hashes to verify
   the 72 source resources independently. Matching the PC source
   still does **not** imply Switch-engine compatibility.
5. After encoded-vs-decoded differences and override
   precedence are known, consider a **single reversible candidate**
   that removes only an evidence-backed problematic override.
   Keep the installed original untouched.

**Status:** Content-level culprit NOT YET PROVEN.
No gameplay fix or ROMFS-only autonomous mounting proof.
