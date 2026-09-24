# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R93

P89 admission remains solved. P90B booted with zero extra trampolines. Runtime first proven action-level divergence: custom fixture 281 requests 708 from caller 0x7725D0 while successful vanilla requests 710 from caller 0x7E6EC8. Custom 708 observed with EA4 0x258 and 0x3E8, so EA4=1000 is not a universal root cause. Static successful path: 0x7E6EA8 MOV W1,#710; 0x7E6EC4 BL 0x766B8C; 0x7E6EC8 checks return.

P91A is read-only, zero-extra-trampoline, parent P89. It reuses existing P50 PlayAction hook and expands pre/post snapshots for E60/E98/E9C/EA0/EA4/BDA4/BDC8/106F4/123E0/123E4 across actions 700..740. No state writes, no force708/710, no char281 gameplay branch, no new hook. Goal: identify the first observable native-state difference at 707->708 versus 707->710 before designing any compatibility bridge.
