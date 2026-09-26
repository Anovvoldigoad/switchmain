NSC P122A — boot-safe static actor+peer C48 readiness bypass A/B

Why:
- P120A proves first custom appended UJ damage reaches bucket5 and is promoted raw15 -> W8=10.
- P121B boots and NOPs peer reject CBZ at main+0x77C4A8, but custom UJ still has no cinematic/710.
- Actor/victim C48 at 0x77C490/0x77C494 executes before peer C48, so P122A opens that reject branch too.

Changes from P121B:
- paired main+0x77C494: 0x34000AC0 (CBZ W0, reject) -> 0xD503201F (NOP).
- paired main+0x77C4A8 remains NOP from P121B.
- both native C48 BLR calls at 0x77C490 and 0x77C4A4 remain intact.
- no additional runtime hooks/trampolines; P120A remains the sole new gate hook.

Deploy BOTH main and subsdk9 from the GitHub Actions artifact.
Fresh boot and confirm:
[NSC:P120A] READY ... patch_ok=1
[NSC:P121B] READY ... patch_ok=1
[NSC:P122A] READY ... patch_ok=1

Test one custom UJ. Do not recover with another attack before saving log.
Expected P120 evidence:
[NSC:P120A] GATE ... bridge=1 ... raw=15 out=10

Decision:
- If cinematic/710 starts: actor C48 reject was the remaining readiness blocker after P120/P121B.
- If still no cinematic: both C48 reject branches are bypassed, so move forward to type9 / 0x7EF098 corridor; do not revisit raw15/24, B9E4, or 708.

This is a causal A/B, not the final generic readiness policy.
