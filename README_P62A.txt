NSC Switch v1.70 — R71 / P62A Persistent UJ Control Getter

PURPOSE
P61 hardware proved the guarded F58 patch never fired. P62 removes that strategy and implements source `enable_control(UJ)` as a persistent semantic at the proven Switch-native control getter.

DEPLOY
Use the workflow to build `subsdk9`. Deploy the workflow artifact's:
  atmosphere/contents/0100FA10190A0000/exefs/main
  atmosphere/contents/0100FA10190A0000/exefs/subsdk9
Do not reuse an older subsdk9.

TEST
1. Vanilla: XA once, then UJ once.
2. Tobi/custom: XA once, then XXA twice, each from neutral.
3. Victim regression: custom character is hit by one vanilla UJ and must remain visible/playable afterward.
4. Exit emulator and run: python3 analyze_p62a_log.py uzuy_log.txt

KEY MARKERS
[NSC:P62A] READY
[NSC:P62A] CTRL_GET_UJ_PERSIST
[NSC:P59A] PLAY_CALL

PASS CRITERION
The analyzer requires persistent getter virtualization to be observed and a custom PlayAction(700). A getter override without Play700 is reported PARTIAL, never PASS.

SAFETY
No F58 override. No forced state 0x87. No forced action700. No 445->700 rewrite. No char==281 gameplay branch. Victim-UJ shadows retained.
