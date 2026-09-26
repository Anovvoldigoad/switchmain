# NSC2Switch Runtime V2C — Dynamic Core Migration

V2C continues from the hardware-PASS V2B lineage. P128 remains the functional safety net.

## Active runtime-resolved entries

- `EVENT236`
- `PLAY_ACTION`
- `CENTRAL_SETTER`
- `CPK_BIND`
- `CHARACODE_GETTER`
- `UJ_SESSION_POST` derived from the unique native `BL` to resolved `UJ_SESSION_OUTER` with corridor shape `MOV X0,X23 ; BL OUTER ; LDR W8,[X20,#0x50]`.

Every migrated target is fail-closed. There is no fallback to the old absolute entry offset.

## Trampoline budget

V2C activates the `CHARACODE_GETTER` trampoline so custom characodes are observed through a resolver-derived entry. To keep total trampoline pressure unchanged from the V2B/P128 lineage, the historical P77 UJ-acceptance probe is no longer installed. P77 was read-only and returned native behavior unchanged; P67 remains the behavioral baseline and P81 remains functional.

Expected marker:

```text
[NSC:P77A] READY ... probe_installed=0 trampoline_reclaimed_for_characode=1 ...
```

## Expected boot markers

```text
[NSC:V2C] READY resolved=7 total=7 ... migrated_hook_entries=6 ... uj_post_derived=1
[NSC:V2C] HOOK name=CPK_BIND source=resolver ... installed=1
[NSC:V2C] HOOK name=CHARACODE_GETTER source=resolver ... installed=1
[NSC:V2C] HOOK name=EVENT236 source=resolver ... installed=1
[NSC:V2C] HOOK name=PLAY_ACTION source=resolver ... installed=1
[NSC:V2C] HOOK name=CENTRAL_SETTER source=resolver ... installed=1
[NSC:V2C] DERIVE name=UJ_SESSION_POST hits=1 ...
[NSC:V2C] HOOK name=UJ_SESSION_POST source=resolver_derived ... installed=1
[NSC:P128A] READY ...
```

## Test order

1. Boot and reach character select.
2. Hover/select Tobi; confirm `[NSC:P50A] CHAR ... code=mtob` appears.
3. Naruto own UJ.
4. Tobi as victim of enemy UJ.
5. Tobi own UJ.
6. Confirm `POST_OUTER ret=1 session_latch=1` and normal control return.

Do not add stale patches or other subsdk builds to this test.
