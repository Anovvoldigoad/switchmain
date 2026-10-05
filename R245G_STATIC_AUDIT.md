# R245G static audit — ccUiCharacterSelect3DModel state-advance gate

Baseline:
- Title: Naruto x Boruto Ultimate Ninja STORM Connections Switch v1.70
- Build ID: `48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39`
- Clean original main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`

## Recovered gate

Source-path/string xrefs place the relevant code in the `ccUiCharacterSelect3DModel` region. The exact function beginning at `main+0x549804` is:

```text
549804 STP X30,X19,[SP,#-0x10]!
549808 MOV X19,X0
54980C LDR X0,[X0,#0xA8]
549810 CBZ X0,54985C
549814 BL  1161C98        ; RegistryProcess A
549818 CBZ W0,54985C
54981C LDR X0,[X19,#0xC0]
549820 CBZ X0,549838
549824 BL  58490          ; +8 then RegistryProcess
549828 CBNZ W0,549838
54982C LDR X0,[X19,#0xC0]
549830 BL  58498          ; +8 then registry state test
549834 CBZ W0,54985C
549838 LDR X8,[X19,#0x80]
54983C LDUR X0,[X8,#-0x18]
549840 CBZ X0,54985C
549844 BL  1161C98        ; RegistryProcess B
549848 CBZ W0,54985C
54984C MOV W8,#1
549850 STR W8,[X19,#0x6C]
549854 MOV W8,#2
549858 STR W8,[X19,#0x5C]
54985C ... RET
```

Wrapper identities from the same clean main:
- `main+0x58490`: `ADD X0,X0,#8 ; B main+0x1161C98`
- `main+0x58498`: `ADD X0,X0,#8 ; B main+0x1161D20`

Therefore an R204J observation of `REGISTRY_PROCESS result=1` for the registry containing `mtobcharsel` proves only one registry is healthy. The state-advance gate itself requires multiple readiness predicates before it writes `+0x6C=1` and `+0x5C=2`.

## R245G probe

R245G preserves the R204J read-only loader/owner/registry/resource hooks and adds only:
- trampoline at `main+0x549804` to log gate entry/exit and pre/post state;
- scoped logging of every `main+0x1161C98` call while that gate is executing;
- trampoline at `main+0x58498` to log the fallback registry-state result.

It does not modify arguments, returns, registry contents, state fields, paths, IDs, CPK binding, or gameplay behavior. The native function is always allowed to execute normally.

## Decision

- target owner ready but no `GATE_ENTER` -> upstream state-machine dispatch does not reach this gate.
- `target_match=1` and a scoped registry call returns 0 -> registry readiness inside the exact state gate is the blocker.
- `GATE_ALT_READY result=0` -> fallback owner-state readiness is the blocker.
- `GATE_EXIT advanced=1` but no `RESOURCE_LOOKUP ... mtobcharsel` -> this state gate passes; move to the next post-state2 consumer-dispatch boundary.
- `advanced=1` and mtob resource lookup appears -> state gate and dispatch reach the resource consumer; continue with the existing chunk/actor decision tree.
