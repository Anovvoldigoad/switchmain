# Compressed Event236 batch: reproducible evidence — 2026-11-20

## Source anchors and scope
- TheLeonX/NSC-ModManager release [2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/releases/tag/2.1.2.1), published 2026-08-30; downloadable RAR SHA256 `bb0a9eb17fef731250fc5f955e6ef526f3c059faacb8ce2ba15c4988ff8ffa7a` as published by GitHub. Release notes mention Switch Projectiles Target; **no Switch ABI inference**. Start/Stop Deflect numeric IDs are not independently verified from these release notes.
- TheLeonX/NSC-Toolbox [6f780cb6814f07e03c16b3e78d97dde4e4368983](https://github.com/TheLeonX/NSC-Toolbox/commit/6f780cb6814f07e03c16b3e78d97dde4e4368983) (2026-08-30); PC parser/editor source, not original Switch engine contract.
- morluto/rea [d380dc2409904edf058db0444a2a9eb29f827d4d](https://github.com/morluto/rea/commit/d380dc2409904edf058db0444a2a9eb29f827d4d) (2026-11-19); generic RE reference, latest upstream now UEFI-oriented; not CPK/consumer ABI proof.
- Pinned original Switch v1.70 `main`: SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`; tracked blob historically `8af900db0d7003255b4ddb3cbd1289cd5a15458e`, **not rehashed or executed here**. No new engine ABI claim.

## Change and falsifiable proof
Parent `d18b446c4a5ee689af6206bdbd52e43c2dc58b11`, code `d360cd62f7758e4ceff7fe1abaef824c13473ceb`. Source mmap SHA256 is checked before parsing one CPK TOC; private `_validated_index` passes the already verified index into each CRILAYLA reencoder. A wrong SHA must raise before TOC parsing; two members must require exactly one converter TOC parse, with no reencoder reparse. The publisher still independently validates the archive, stages and verifies output; no claim of one TOC parse across **all** independent verification stages. All tests use synthetic CPK fixtures.

Compressed workflow [run 44618894253](https://github.com/Anovvoldigoad/switchmain/actions/runs/44618894253), job `135894875213`, COMPLETED SUCCESS, original log read: 6 candidate, 13 batch, 32 verifier, 12 same-size tests, all OK. Foundation and MovesetPlus run IDs `44618894255` and `44618894295` require independent final-log inspection before calling their jobs PASS.

## Safety and remaining blockers
No runtime hook, original game write, or Uzuy test. Consumer ABI, engine ownership/lifecycle/callback/locks/async/rollback/destructor, archive precedence, genuine mod CPK and gameplay remain unproven. Sakura aura107, Event236 marker 0x4E53 at +0x2A and native unmarked behavior unchanged. `full_moddingapi=false`, `ready_for_gameplay_test=false`, `emulator_tested=false`.
