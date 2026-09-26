# NSC2Switch MASTER CHECKPOINT — R143 / P127A
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
main Build ID: 48ece454b61412b9fb46fab2be3f5ef7b2804f39

## P126 runtime result
- Uploaded compiled artifact main SHA256: 9ff3494b52a3ed2fd9af8879bbeec47806134a7607954c02ba622c2150fc06cf.
- Uploaded compiled artifact subsdk9 SHA256: f682739052b37dba092e9abcdcd21dc0401054c0799264bb0db9b83d77e99c07; NSO build ID 920bcb2df6c48cd053ff6c0c5238b1b2495849ac.
- P126 READY confirms actor reject static patch architecture loaded.
- Custom Tobi reaches P124 GATE bridge=1 on appended idx1848 raw15->10.
- No filtered AFTER_ACTOR/AFTER_PEER/TYPE9/POST_OUTER marker is printed.
- Tobi then takes natural707->708 and P125 cleanup reports session=0,mature=0,E94=63,E98=136,BDA4=1,out125.
- Naruto successful native710 path remains present in the same log.

## Important correction
P126 main is verified to contain 0x77C494=Nop. Therefore absence of P124 AFTER_ACTOR cannot be treated as proof that the branch patch did not execute. P124ReadFocus re-validated transient semantic/opposite-side state after native helpers. That filter can suppress reach markers even when the already-qualified custom actor is still the same actor.

## P127A design
- Strict arm condition is unchanged: generated/custom actor, semantic UJ, action707, opposite-side victim, appended damage record, native event type not already10/11.
- Downstream reach/session observation trusts only that already-qualified actor latch plus custom identity; it does not re-require transient semantic/opposite fields.
- Paired main opens all remaining known branch exits before outer session setup while preserving every native call:
  - 0x77C494 = NOP (actor C48 reject open)
  - 0x77C4A8 = NOP (peer C48 reject open)
  - 0x77C4B4 = B 0x77C514 (force type9-zero success path)
  - 0x77C520 = B 0x77C59C (force lookup-null success path)
- Native calls at 0x77C490, 0x77C4A4, 0x77C4B0, 0x77C51C, 0x77C5E8 remain byte-for-byte intact.
- P125's session-qualified state137 fallback remains guarded by native 0x7EF098 success plus mature actor context.

## Safety / interpretation
P127A is a functional causal A/B, not the final generic policy. If it restores cinematic, the final fix must move upstream and reproduce whichever native readiness/session semantics were missing rather than retaining global branch forcing.
