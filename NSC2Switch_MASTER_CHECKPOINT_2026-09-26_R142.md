# NSC2Switch MASTER CHECKPOINT — R142 / P126A
Date: 2026-09-26
Target: Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
Program ID: 0100FA10190A0000
Build ID main: 48ece454b61412b9fb46fab2be3f5ef7b2804f39
Restore main SHA256: 2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

## P125 runtime lock
Uploaded runtime artifact main matches baseline paired main SHA256 1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0.
P125 READY loaded. Naruto UJ is user-confirmed safe.
Custom Tobi own-UJ:
- P124 GATE bridge=1 for idx1848/raw15 -> out10 at action707.
- No P124 AFTER_ACTOR marker appears.
- No AFTER_PEER / TYPE9_ZERO / P125 POST_OUTER appears.
- Later P125 CLEANUP records action708, session=0, mature=0, E94=63,E98=136,E9C=0,BDA4=1,BDA8=0, request125 stays125.

Conclusion: first proven native reject after the corrected event-type gate is actor C48 return zero at main+0x77C490 followed by CBZ at0x77C494. P125 correctly refuses the P107 endpoint because native session setup never succeeded.

## P126A design
Single causal A/B only:
- preserve native actor C48 BLR at0x77C490;
- paired main patches only 0x77C494 CBZ W0,0x77C5EC -> NOP;
- peer C48 BLR + peer reject at0x77C4A4/0x77C4A8 remain native;
- type9, lookup, 0x7EF098 remain native;
- P125 POST_OUTER/session-qualified cleanup137 fallback remains intact;
- zero P126 hooks/trampolines; no char281 branch; no force708/710.

Paired P126 main SHA256: 9ff3494b52a3ed2fd9af8879bbeec47806134a7607954c02ba622c2150fc06cf.

## Runtime decision
- GATE -> AFTER_ACTOR but no AFTER_PEER: peer C48 is next blocker.
- AFTER_PEER but no TYPE9_ZERO: type9 preflight is next blocker.
- TYPE9_ZERO but no POST_OUTER: blocker is 0x77C514..0x77C5E8 pairing/lookup corridor.
- POST_OUTER ret!=0: native session setup succeeded; P125 can qualify later cleanup only if mature.
- CLEANUP bridge=1 followed by native710/cinematic: P107 endpoint reused only after native setup.
