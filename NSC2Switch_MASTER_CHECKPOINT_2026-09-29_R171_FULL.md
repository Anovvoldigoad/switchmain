# NSC2Switch MASTER CHECKPOINT — R171
Date: 2026-09-29

## Locked target
- STORM CONNECTIONS Switch v1.70
- Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- original main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- R164 StageInfo/CPK remains frozen hardware-PASS.
- P128 exact 30-word main delta remains frozen.
- Voice and D-pad remain out of this iteration.

## R170 hardware result
R170 was read-only and hardware-valid. The exact action707 completion gate at `main+0x769A4C`, called from `main+0x7E48E8`, repeatedly returned zero. Every captured row classified the blocker as `anim_flag70`: `anim+0x70 bit0` stayed set while `busy1264=0` and the animation timer advanced normally. The actor later reached E94/E98=8/8 with action still707.

## Hit-path safety reference
A proven successful Tobi UJ handoff reaches PlayAction710 from action707 with E94/E98=137/136 and BDA4=0. Therefore the R171 terminal whiff guard E94/E98=8/8 + BDA4=1 excludes that proven hit path.

## R171 functional candidate
Same native gate hook/fingerprint as R170. On exact conditions only:
- custom generated OugiAwakening member
- semantic UJ active
- side0
- caller return `0x7E48E8`
- action707
- E80=1
- E94=8
- E98=8
- E9C=0
- BDA4=1
- actor+0x1264=0
- animation object and inner+0x50 valid
- anim+0x70 bit0 is set
- reconstructed native timing predicate already passes

R171 clears only bit0 of `anim+0x70`, preserving the remaining 15 bits, then calls original `0x769A4C` once. It never requests action708/710 itself. The expected native caller behavior is ret!=0 -> lookup708 -> native vslot+0xF98 -> action708.

## Hardware markers
Expected release:
`[NSC:R171] UJ707_FLAG_RELEASE ... match=1 ret=1 flags70=0001->0000 ...`
Then verify native logs show action707->708 without a direct R171 action injection.

## Retired
- R167 a2 rewrite
- R168 direct animation bounce
- R169 707->77->74 symptom workaround
- R170 read-only provenance probe (superseded by R171 candidate)
