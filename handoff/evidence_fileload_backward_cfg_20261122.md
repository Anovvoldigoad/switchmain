# FileLoad backward CFG witness — 2026-11-22

Source references: [NSC-ModManager 2.1.2.1](https://github.com/TheLeonX/NSC-ModManager/blob/2.1.2.1/README.md) README blob 8e9560b2e906fa88ae8aca20f99e3f3e77fbf709 (Steam-only); [NSC-Toolbox 2.1.2.1](https://github.com/TheLeonX/NSC-Toolbox/blob/2.1.2.1/README.md) README blob 657f161390c4abe8afe10cea11a2b9a28e6bf6b0 (PC editor). Generic REA reference not independently refreshed (404 on attempted repository); none of these establishes Switch engine ABI.

Pinned original Switch v1.70 main expected SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9; no local original-byte rehash. Existing Foundation workflow runs a pinned-byte guard, but no HEAD log is available yet.

Falsifiable hypothesis: a stack write at a higher virtual address may reach a matching stack read at a lower virtual address via a backward CFG edge. Existing numeric PC ordering excluded such candidates even when a path exists. Synthetic instruction sequence SUB SP,#16; B writer; LDR X2,[SP,#8]; B exit; STR X1,[SP,#8]; B reader; RET must produce a candidate with writer 0x3810, reader 0x3808 and witness [0x3810,0x3814,0x3808]. Replacing the backward branch with a forward branch to RET must produce zero candidates. Neither case proves executed-path dataflow, pointer ownership, callback, lock, async, rollback, unbind, destructor, archive precedence or native consumer ABI.

Source change removes numeric PC ordering from the candidate filter while preserving distinct writer/reader PCs and the bounded CFG witness. Static/host/ARM64/Uzuy: not verified for this HEAD. No game runtime changes.
