# P39 — upstream draw/submit coverage after P38 trace shows zero calls

## Grounding: user Uzuy log from 24 October 2026

The user's new log `uzuy_log(1).txt` contains two emulator sessions.
The P38 session starts at **2577.75 s**; the earlier session at **4.37 s**
uses P32/P34 and must not be confused with the P38 runtime.

Confirmed second session:
- `[NSC:P38] READY installed=1` and
  `[NSC:P38] STATUS cpk=1 xfbin_trace=1 render_probe=1` at 2577.754;
- `[NSC:P32] CPK_BIND ... result=1` at 2580.083;
- `[NSC:P38] ARM char=281 code=mtob` at 2583.129;
- `mtob` assets open/read through 2708.815, but there are **zero**
  `[NSC:P38] CHILD`, `BRIDGE`, or `PRODUCER` markers from the
  confirmed P38 session.

This negative result is only evidence that **the three R266 function
entrypoints never emitted a tracked callback after ARM**. It does
**not** prove that the enemy's actor or model is absent; it could be
a distinct native draw/registration path. Approximately 17 GPU memory
unmapped-read messages around 2713.55–2714.19 also occur in this run.
Without an unmodded matched control, they cannot be causally assigned
to opponent disappearance or blamed on the driver.

## Technical step: two upstream checkpoints

P39 keeps the P37/P38 loader and render-stage probes and adds:
- `[NSC:P39] DRAW` — R264 native model draw at `main+0x54ADA0`,
  captures actual model pointer and `identity38`, with `base90` and
  `secondary98` pointers.
- `[NSC:P39] SUBMIT` — R265 draw submit at `main+0x5B3AC`,
  captures `slot`, `identity` and call counts for all three P38
  render-stage probes.

Both hooks require exact Switch 1.70 fingerprint matches before installation
and invoke `Orig` exactly once. Logging begins only after
`characode 281 == mtob` is observed, bounded to 192 events each.
There are no game-memory writes, CPK modifications, main NSO edits,
path rewrites, or forced rendering flags.

### Decision table

| Runtime observation | Next point of investigation |
| --- | --- |
| P39 `READY installed=0` | Wrong native fingerprints or loaded main; do not interpret absent events |
| P39 draw + submit both absent, P38 events absent | Legacy R264–R266 path does not cover this battle; trace earlier actor-to-model dispatch |
| P39 draw present but submit absent | Inspect the native draw branch leading to submission |
| P39 draw and submit present but P38 events absent | Investigate state/registration of the resulting draw model, and which native producer callsite is truly active |
| P39 submit present, model pointer null | Investigate actor/model binding before draw submit |
| P39 events present | Compare specific `identity38`, `slot` and model-pointer sequences; never label an identity as Tobi/opponent without matched control |

**Important:** Neither lack of a log nor a `main+offset` match is itself
a playable character fix. The earlier P128A cinematic/UJ patches were not
portably relevant to actor rendering and remain excluded.

## GitHub Actions

`.github/workflows/build-subsdk9-p32.yml` builds this branch using
pinned exlaunch and devkitPro; artifact expected:
`NSC-P39-Tobi-upstream-draw-submit-probe-subSDK9`.

Runtime use only as a **replacement for the existing P38 subsdk9**, not
alongside it. Leave the P37 carrier and original stock main unchanged.
Preserve the original working `subsdk9` as backup.
**No playable fix is claimed.**
