# NSC2Switch Runtime R167 — Custom UJ Miss Animation Refresh

Target: STORM CONNECTIONS Switch v1.70, Build ID 48ece454b61412b9fb46fab2be3f5ef7b2804f39.

R167 fixes one exact custom-UJ whiff cleanup signature observed on hardware:
- custom actor (`char_id > vanilla max`, no Tobi-specific ID branch)
- semantic UJ active
- native cleanup request `PlayAction(74)`
- incoming animation parameter `a2=-1`
- pre-action `740`
- caller return offset `main+0x798F34`
- actor `e80=1`
- actor `bda4=1`

For that exact signature only, R167 forwards `a2=0` to the same native PlayAction call. This mirrors a native neutral-refresh form at main+0x63A500 while preserving a single native call and every other argument/state transition.

Frozen / unchanged:
- original main on disk
- resolver 7/7 + validate-before-write 30-word runtime patch
- P128 admission/session
- R164 StageInfo CPK
- stage bridge / registry path
- opcode26 SFX
- D-pad/Izanagi
- voice behavior (R165/R166 voice probes are NOT installed in R167)

Expected log marker on a Kamui miss:
`[NSC:R167] UJ_MISS_ANM_REFRESH phase=pre ... a2=-1->0 pre=740 e80=1 bda4=1 ...`
followed by a `phase=post` marker with `post=74`.

Test:
1. Keep Tobi_Switch R164 CPK.
2. Build/install R167 runtime.
3. Fresh boot.
4. Use Tobi UJ and intentionally miss completely.
5. Do not touch movement for 3-5 seconds. The Kamui animation should terminate without requiring input and should not accumulate lag.
6. Then run one UJ that hits to confirm the hit path remains unchanged.
