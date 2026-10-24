# P38 — Tobi native render-registration probe (Switch 1.70)

## Why this exists

**Observed on user's Uzuy:** The P37 carrier loads and the game boots, but the
opponent remains invisible in Tobi battles. Three stock-restored globals
`conditionprm`, `damageprm`, and `privateCamera` did not cure visibility.
The P34 load trace had 50 successful custom-character file opens and reads,
but never traced native model registration or final render.

## Exact comparison against historic Actions artifacts

- **P128A** artifact run `36240507170` packages a **paired patched main**
  and `subsdk9`. It implements cinematic/UJ gate changes (P125–P128); there
  is *no proven causal evidence* that these specific main patches fix opponent
  rendering in P37. Do not transplant them by assumption.
- **V2D** artifact run `36255430668` packages original main + `subsdk9`.
  Its native resolver applies 30 in-memory patch words for condition count,
  P67, and cinematic P128 parity after signature verification. Again, no
  demonstrated render visibility fix.
- **R265** run `37349787809` traces render object gating; prior R265
  reports describe zero objects in a targeted draw submit.
- **R266** run `37353842961` traces model-child creation, registration
  bridge and render producer. However historical R266 targets model
  `identity38==46`, not established as Tobi. The R265/R266 experiments
  are **not automatically comparable** to the 24-Oct P37 Tobi battle.

### What P38 actually changes

P38 keeps *all* existing P34/P37 CPK mount and XFBIN load hooks and adds
**three read-only hooks** with offsets and fingerprint words from R266:

| Native point | Offset | Output |
| --- | --- | --- |
| model child create | `0x6ECEE8` | `[NSC:P38] CHILD` with model identity, selector, count |
| registration bridge | `0x6ED110` | `[NSC:P38] BRIDGE` with identity, count |
| render producer | `0x594D8` | `[NSC:P38] PRODUCER` with mode, slot, identity |

To avoid the **false identity46 assumption**, these trace the real native
identity values from registration and producer calls after
`characode 281 == mtob` has been observed. They *do not* claim all logged
models belong to Tobi or to the opponent; their identities must be
correlated with runtime and baseline controls. The output is capped at
512 entries per hook (up to 1536 messages). Original code is always
called once without replacing return values. All 3 hooks are installed
only when every signature matches and P34 CPK/load tracing is installed.

**Nothing is modified in the main NSO or the game's CPK, actor memory,
visibility flags, camera or rendering state.** This is an instrumented
binary candidate, not a playable fix. Game integrity and update version
still require runtime validation before any trust in the signatures.

## Build in GitHub Actions

The branch `research/p38-tobi-render-registration-probe` modifies the
existing build workflow `.github/workflows/build-subsdk9-p32.yml` to
build `NSC-P38-Tobi-render-registration-trace-subsdk9` using the pinned
exlaunch revision `229bbd6` and devkitPro. Tests include
`test_analyze_p34.py` and `test_p38_source.py`.

Expected artifact path, **once Actions succeeds**:

```text
atmosphere/contents/0100FA10190A0000/exefs/subsdk9
SHA256SUMS.txt
README_P38.md
```

Do not mix this `subsdk9` with the older R181/P128 patched main.
Use only the original game's main for the current P37 ROMFS arrangement.

## Runtime comparison protocol (not completed)

1. Preserve a copy of the working P37 `subsdk9` and P37 carrier. Use P38
   `subsdk9` only as a **single-variable** test on same Uzuy/driver,
   battle map, and opposing character; do not install both overlay loaders.
2. Confirm `[NSC:P38] STATUS cpk=1 xfbin_trace=1 render_probe=1` and
   `[NSC:P38] ARM char=281 code=mtob` in Uzuy log. A `render_probe=0`
   means the hooks **did not install** and runtime conclusions are invalid.
3. Compare `CHILD`, `BRIDGE`, and `PRODUCER` and their identity/count
   sequences against a matched vanilla opponent control. The first missing
   stage is a candidate to inspect next, not proof of the faulty asset.
4. Restore known-bootable `subsdk9` if P38 fails to boot, crashes, or changes
   the rendering issue. Do not delete the source CPK, use P36's altered
   encoding, or force the P128 cinematic bypass.

## Status

Only checked-in native source and historical Actions are verified at authoring
time. P38 compiling and Uzuy runtime both require separate evidence.
No gameplay fix is claimed.
