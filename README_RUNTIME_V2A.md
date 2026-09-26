# NSC2Switch Runtime V2A — DynamicResolver Coexistence Probe

Purpose: begin migrating the working P128 runtime away from `main+hardcoded_offset` while preserving P128 behavior as a safety net.

## What V2A changes

- Adds a read-only ARM64 masked-word signature scanner.
- Resolves seven semantic anchors from the mapped `main` text:
  - CHARACODE_GETTER
  - CPK_BIND
  - EVENT236
  - PLAY_ACTION
  - CENTRAL_SETTER
  - UJ_SESSION_OUTER
  - STATE137_CONTROLLER
- Fails closed if a signature has zero or multiple matches.
- Does not install any hook from a resolved address yet.
- Does not write game memory.
- Contains no Tobi/char281 branch.
- Runs the proven P128 installer after the V2A resolver so current gameplay behavior stays intact.

## Why subsdk9 still exists in V2A

V2A uses the current exlaunch/subsdk9 path only as a bootstrap to test the new resolver inside the game process. It is not the final loader architecture.

Migration plan:

1. V2A — resolver read-only, P128 unchanged.
2. V2B — migrate one safe native hook (EVENT236/PlayAction) to resolver-selected address.
3. V2C — migrate remaining functional hooks and static UJ corridor patches; restore original `main`.
4. V2D — move the same loader-agnostic runtime core behind an external plugin/injection bootstrap; remove the subsdk9 dependency.

This order separates address-resolution bugs from loader bugs and preserves the current functional UJ checkpoint.

## Expected log

```text
[NSC:V2A] RESOLVER_START ...
[NSC:V2A] RESOLVE name=CHARACODE_GETTER hits=1 ... exact=1
[NSC:V2A] RESOLVE name=CPK_BIND hits=1 ... exact=1
[NSC:V2A] RESOLVE name=EVENT236 hits=1 ... exact=1
[NSC:V2A] RESOLVE name=PLAY_ACTION hits=1 ... exact=1
[NSC:V2A] RESOLVE name=CENTRAL_SETTER hits=1 ... exact=1
[NSC:V2A] RESOLVE name=UJ_SESSION_OUTER hits=1 ... exact=1
[NSC:V2A] RESOLVE name=STATE137_CONTROLLER hits=1 ... exact=1
[NSC:V2A] READY resolved=7 total=7 ...
[NSC:P128A] READY ...
```

On v1.70 all seven should resolve uniquely to the known reference offsets. On a future build, `exact=0` is acceptable if `hits=1`; the important property is a unique validated match. V2A still uses the v1.70 scan span; dynamic RX-region discovery is scheduled before the external-loader stage.

## Build

```bash
python3 verify_runtime_v2a.py
git add -A
git commit -m "Runtime V2A dynamic resolver coexistence probe"
git push
```

GitHub Actions artifact:

`NSC-RUNTIME-V2A-resolver-coexistence`

For V2A only, deploy both `main` and `subsdk9` from the artifact because P128 is intentionally kept as the gameplay safety net. Do not delete the working P128 backup.
