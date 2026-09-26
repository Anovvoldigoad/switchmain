# NSC2Switch Runtime V2B — Dynamic Hook Entry Migration

V2B keeps P128 gameplay behavior while migrating the hook ENTRY addresses for:
- EVENT236
- PLAY_ACTION
- CENTRAL_SETTER

These three installers consume addresses produced by the runtime signature resolver.
There is no hardcoded-offset fallback for those entries. If an anchor is missing or ambiguous,
that hook fails closed. Other P128/P89/P81/helper dependencies are intentionally still legacy in
this stage and will be migrated incrementally.

Expected boot markers:
```
[NSC:V2B] READY resolved=7 total=7 ...
[NSC:V2B] HOOK name=EVENT236 source=resolver ... installed=1
[NSC:V2B] HOOK name=PLAY_ACTION source=resolver ... installed=1
[NSC:V2B] HOOK name=CENTRAL_SETTER source=resolver ... installed=1
[NSC:P128A] READY ...
```

Test: Naruto UJ -> Tobi victim UJ -> Tobi own UJ.
