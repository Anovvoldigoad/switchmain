NSC2Switch — P60A Native UJ Control Port (R69)
================================================
Target: Naruto x Boruto Ultimate Ninja Storm Connections Switch v1.70
Program ID: 0100FA10190A0000
Paired main SHA256: 8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be
Pinned exlaunch: 229bbd6

WHY THIS BUILD EXISTS
---------------------
P59 hardware proved vanilla UJ and the broken custom route diverge before
PlayAction:
- Kakashi XA: e94=0x4D -> PlayAction445.
- Kakashi UJ: e94=0x87 -> PlayAction700.
- Tobi XA and both Tobi XXA attempts: e94=0x4D -> PlayAction445.

Binary audit then found the Switch-native indexed control API:
- getter 0x7C6280
- enable setter 0x7C65B0
- control object = actor+0x228
- UJ router reads native selector 8 and selects state0x87.

The custom moveset already asks Event236 op14 p2=0 p3=1 (enable UJ control),
but the inherited bridge previously shadowed that request while returning success.

P60A FUNCTIONAL DELTA
---------------------
ONLY this mapping is enabled:
  MovesetPlus Event236 op14 p2=0 p3=1
      -> Switch NativeEnableControl(actor+0x228, selector 8)

Everything else stays as P59/P50:
- other op14 selectors: shadow
- op15/17/18: shadow
- visibility op12: shadow
- no 445->700 rewrite
- no e94/state force
- no char281 special-case

FAIL-CLOSED GUARD
-----------------
P60A fingerprints 0x7C6280 and 0x7C65B0 before installing the functional map.
If either does not match the pinned v1.70 executable, native_uj_control remains 0
and op14 falls back to shadow behavior.

EXPECTED LOG
------------
Boot:
  [NSC:P60A] READY ... native_uj_control=1 ...

When the custom moveset asks UJ enable:
  [NSC:P60A] CTRL14_UJ_PORT ... mp_selector=1 native_selector=8 before=X after=1 ...

P59 diagnostics remain active:
  [NSC:P59A] PLAY_CALL
  [NSC:P59A] MODE_BASE
  [NSC:P57A] SETTER

TEST PROTOCOL
-------------
Vanilla control character (Kakashi is fine):
1. Neutral -> XA once -> wait neutral.
2. UJ once -> let it finish.

Tobi/custom:
1. Enter the same True Awakening/setup used in P59.
2. Neutral -> XA once -> wait until complete.
3. Neutral -> XXA once -> let the resulting sequence finish.
4. Neutral -> XXA once again -> let it finish.
5. Regression: let the vanilla opponent's UJ hit Tobi; after cinematic verify
   Tobi remains visible and playable and the enemy remains visible.
6. Exit cleanly and save the complete Uzuy log.

SUCCESS CRITERIA FOR THE ROOT FIX
---------------------------------
Required:
- P60A READY native_uj_control=1.
- CTRL14_UJ_PORT shows native selector8 after=1.
- Tobi XA remains ordinary jutsu / PlayAction445.
- Tobi XXA reaches PlayAction700 / UJ progression instead of collapsing to 445.
- victim-UJ visibility/playability regression remains PASS.

Use:
  python3 analyze_p60a_log.py uzuy_log.txt

If slot8 becomes 1 but XXA still remains 445, do NOT force 700. That result means
another upstream gate exists and the log becomes the basis for the next exact
native mapping.

NOTE ON AWAKENING
-----------------
P60A does not claim to fix Awakening. The moveset requests additional control
selectors, but their Switch-native mappings have not yet been proven. They remain
shadowed deliberately rather than guessed.
