# R267 Static Audit — Secondary Inner Binding / Base Model Draw

## Correction from R265/R266

The `main+0x5B3AC` submit reached after the character-select Draw wrapper is an accessory/child render path in this context. The R252 `self+0x188..0x190` Wait vector feeds `main+0x54ADE8`, which builds `data/accessory/<name>.xfbin` and ultimately calls the shared producer `main+0x594D8`. Therefore an empty accessory submit entry does **not** establish a missing base-character renderer.

The actual character body is drawn earlier in the same Draw callback:

`main+0x54ADA0 -> main+0x54ABC4 -> model vtable+0x28 -> main+0x6ECAE4`.

The model vtable target `main+0x6ECAE4` was resolved offline from NSO RELA relocations. Constructor `main+0x6EA398` installs the model vtable at `0x204FDF0`; relocation slot `0x204FE18` (`vtable+0x28`) resolves to `0x6ECAE4`.

## Exact base draw predicate

`main+0x6ECAE4`:

```asm
6ECAF0  LDR X0,[model,#0x98]
6ECAF4  CBZ X0,6ECB20
...
6ECB10  LDR X8,[X0,#0x18]
6ECB14  CBZ X8,6ECB2C
6ECB18  BL  0x117E0D8
```

R264 already hardware-proved `model+0x98 != NULL`. Therefore the unresolved predicate is `secondary98+0x18`.

## Exact source of secondary98+0x18

The secondary object's derived setup path resolves to `main+0x117D2E8`, which calls `main+0x1182C60`; the first operation in `0x1182C60` calls `main+0x118001C`.

`main+0x118001C` contains the direct binding:

```asm
1180038  LDR X8,[X1,#0x08]   ; typed nuccChunkAnm + 0x08
118003C  STR X8,[X0,#0x18]   ; secondary object + 0x18
```

For the R264/R263 target, `X1` is the typed `mtobcharsel00` object returned non-null by `main+0x120A3D4`, and `X0` is the secondary object later stored at `model+0x98`.

Thus:

`secondary98+0x18 == typed_mtobcharsel00+0x08`.

The outer typed chunk pointer being non-null does not prove its inner `+0x08` binding is non-null. Serialized XFBIN comparison cannot directly reveal this runtime pointer; it is a loader-created object field.

## R267 decision

R267 is read-only and measures only the exact unresolved runtime boundary:

1. `typed_mtobcharsel00+0x08` before the copy;
2. `secondary98+0x18` after the copy;
3. the base model draw predicate at `main+0x6ECAE4`;
4. whether `main+0x117E0D8` is actually reached.

No CPK binding, path rewrite, ID patch, state force, return override, or game-main patch is performed.
