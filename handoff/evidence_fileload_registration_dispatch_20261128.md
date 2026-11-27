# FileLoad registration callee dispatch-flow evidence — 2026-11-28

## Basis

This slice extends the verified original-main trace in handoff/evidence_fileload_registration_callee_20261128.md. Research sources remain the current NSC-ModManager/NSC-Toolbox 2.1.2.1 and 2.1.2.0 tag comparisons, PyCriCodecs CPK/UTF reference, REA static-analysis methodology and pinned Switch v1.70 main. No upstream parser ABI delta was found in the inspected skill/XFBIN files. Exact source refs and Git blob IDs are recorded in the preceding evidence note.

Original main Git blob 8af900db0d7003255b4ddb3cbd1289cd5a15458e, 27,701,509 bytes; required SHA256 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9.

## Falsifiable instruction/dataflow facts

The 0x116b390 bounded CFG is pinned to [0x116b390,0x116b590). Exact instructions show X19<-X0 at 0x116b398; direct BL edges 0x116b39c->0x116b7b0, 0x116b3a4->0x116d380 and 0x116b3b0->0x116b82c; W1<-W0 at 0x116b3a8; X0<-X20 at 0x116b3ac; CBZ X19 at 0x116b3b4; CBZ X0 at 0x116b3b8; X8<-mem[X0] at 0x116b3bc; X1<-X19 at 0x116b3c0; X2<-mem[X8+0x58] at 0x116b3c4; and BR X2 at 0x116b3d0. The BR target is not resolved.

The alternate branch at 0x116b3ec targets 0x116d820 after X0<-X19 at 0x116b3e0. The local stack pattern begins with STR X30,[SP,#-0x20]! and STP X20,X19,[SP,#0x10], then restores X20/X19 and X30 before either BR X2, RET, or the alternate B. This is a local stack observation, not complete function/lifecycle proof.

Four separate 0x100-byte bounded target windows are recorded for 0x116b7b0, 0x116d380, 0x116b82c and 0x116d820. They are not assumed to be full function extents. Raw B/BL inbound candidates are census evidence only.

## Limits

The BR X2 target is unresolved. The analyzer does not identify a vtable, callback, destructor, release routine, object type, lock/unlock, async behavior, rollback/unbind, consumer ABI or archive precedence. It does not install a hook or claim runtime compatibility. All release flags remain false.

## Implementation

- Source: tools/portlib/native_fileload_registration_dispatch.py
- Source blob: c8897caaacebb6d96eca351bcf775cd5cd468434
- Test: tests/test_native_fileload_registration_dispatch.py
- Test blob: d16853b274be4c2a30a6f91141bfc8f615e6d236
- Workflow: .github/workflows/verify-port-foundation.yml
- Workflow blob: 766ec521f3214393c84afb8c6dd54ff69e34bc84
- Parent HEAD: dffbf1bd2fc5257a72279186545bbd8d956ab0fe
- CI state: PENDING_CI