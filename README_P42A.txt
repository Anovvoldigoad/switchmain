NSC2Switch P42A — O14 SHADOW LOCK + KAMUI OPCODE ISOLATE

Parent: P41A hardware result

P41A conclusions locked:
- Victim-UJ PASS with O14 not calling broken native
- CTRL_DUMP rejected actor+0x12A24 as PC-style boolean control block
- OUGI_CALLER=0 and OUGI_CORE=0 during Kamui -> path is upstream of UJ core
- EVT13_AWAKE=0 -> awakening still upstream of Event13
- StageMove PASS

P42A gameplay delta vs P41A:
1. O14 -> pure shadow (CTRL14_SHADOW). Removes rejected direct-write candidate.
2. OP15 / OP17 / OP18 -> explicit shadow handlers with dedicated markers
   (previously 17/18 fell through default; now countable for Kamui sessions).
3. CTRL_DUMP removed from runtime path.
4. Event13 / Event121 / OugiCore / OugiCaller traces retained (read-only).
5. O12 remains shadow; O2 StageMove and other proven handlers unchanged.
6. No Tobi/281 gameplay hardcode; custom route remains generic >280 && <0x1000.

Expected READY:
[NSC:P42A] READY ... ctrl14_shadow=1 op15_shadow=1 op17_shadow=1 op18_shadow=1 ougi_caller=1 ...

Hardware test:
1. Boot, verify READY, no fingerprint FAIL
2. Tobi vs Naruto slot1 enemy UJ -> victim must remain PASS
3. StageMove once -> PASS
4. Tobi Kamui UJ once; leave stuck several seconds
5. Optional awakening attempts
6. Full fresh Uzuy log

What to extract from log:
- CTRL14_SHADOW counts (should be high; victim-UJ still PASS)
- OP15_SHADOW / OP17_SHADOW / OP18_SHADOW around Kamui timestamp
- OUGI_CALLER / OUGI_CORE / EVT13_AWAKE still expected 0 until new boundaries

Next after P42A log:
- If victim-UJ stays PASS: O14 shadow is the locked production policy for now
- Use OP15/17/18 sequence timing to plan a single-opcode live A/B
- Do not re-enter ougi core patches until a path that actually calls them is found

Restore main SHA256:
2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9
