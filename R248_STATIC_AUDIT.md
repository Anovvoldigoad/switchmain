# R248 static audit — Create-state model identity/readiness producer

Baseline:
- Naruto x Boruto Ultimate Ninja STORM Connections Switch v1.70
- Build ID: `48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39`
- clean original main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

## Hardware prerequisite from R247 / uzuy_log(31)
Target Load reaches state2, Create::enter produces a non-null model, but Create::update remains state2 for the entire target hover and target never enters Wait or Select.

## Exact Create update predicate
`main+0x54991C`:

```text
54991C STP X30,X19,[SP,#-0x10]!
549920 MOV X19,X0
549924 LDR X0,[X0,#0xB0]        ; model
549928 CBZ X0,549944
54992C BL  6ECBB0               ; readiness predicate
549930 CBZ W0,549944
549934 MOV W8,#1
549938 STR W8,[X19,#0x6C]
54993C LDR W8,[X19,#0xD0]
549940 STR W8,[X19,#0x5C]
549944 ... RET
```

`main+0x6ECBB0`:

```text
6ECBB0 LDR X8,[X0,#0x90]
6ECBB4 CMP X8,#0
6ECBB8 CSET W0,NE
6ECBBC RET
```

Therefore the target remains in Create/state2 exactly when `model+0x90` is null.

## Producer of model+0x90
Create::enter `main+0x549868` allocates/constructs the model at `[self+0xB0]`, looks up a descriptor using `self+0xCC` through `main+0x64ED30`, initializes model identity fields, then calls `main+0x6EAC24`.

The descriptor-to-model mapping in this path is:
- descriptor +0x04 -> model +0x38
- descriptor +0x08 -> model +0x3C
- descriptor +0x18 -> model +0x44
- descriptor +0x1C -> model +0x48
- self +0x144 -> model +0x40
- self +0x10C -> model +0x4C

Inside `main+0x6EAC24`:

```text
6EAC44 MOV X0,X19
6EAC48 BL  6EA7B0               ; reset/cleanup
6EAC4C LDR W0,[X19,#0x38]       ; identity
6EAC50 BL  3F4130               ; identity/database lookup
6EAC54 CBZ X0,6EB018            ; null -> epilogue, no +0x90 store
...
6EAD98 STR X21,[X19,#0x90]      ; successful object creation
```

`main+0x3F4130` reads the global manager chain, passes the input identity to the native table lookup, and returns its pointer result.

## R248 probe
R248 is read-only and installs only six diagnostic hooks:
1. target mtobcharsel registry capture;
2. Create::enter `main+0x549868`;
3. descriptor lookup `main+0x64ED30`;
4. model init `main+0x6EAC24`;
5. identity lookup `main+0x3F4130`;
6. exact Create readiness predicate `main+0x6ECBB0`.

No state writes, return overrides, identity remaps, path rewrites, CPK binding, or gameplay patches are added.

## Decision tree
- `IDENTITY_LOOKUP result=null` for target -> blocker is the identity/table input used by model init; inspect descriptor/`model+0x38` provenance next.
- identity lookup non-null but init post still `ready90=null` -> blocker lies after the database lookup in model object allocation/initialization.
- init post `ready90!=null` and ready predicate returns1 -> Create readiness passes; resume Create->Wait progression.

Important: the old unaudited `mtobprm` internal-character-ID question becomes relevant only if R248 proves the target identity/table lookup is null. Do not rewrite 281->46 blindly before that proof.
