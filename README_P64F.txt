NSC2Switch P64F — UJ SEMANTIC BRIDGE (FUNCTIONAL A/B)

THIS IS NOT A READ-ONLY BUILD.

Purpose
-------
P63 proved Tobi XXA still resolves to ordinary jutsu / state 0x4D / PlayAction445
and never reaches the normal downstream UJ gate. P64F connects the source-level
MovesetPlus "Enable Control selector1 = Ultimate Jutsu" semantic to a newly
static-proven Switch 1.70 native consumer.

Why this consumer
-----------------
main+0x7ABE9C directly queries the native control getter with selector1 at
0x7ABF30. That helper is directly called from the UJ router at 0xC76C0,
0xC76EC and 0xC78D0. This is stronger than the rejected selector8 theory:
P64F does NOT globally reinterpret a Switch native selector number.

Functional change
-----------------
1. Event236 op14 / selector1 -> remember UJ-enabled for the target actor.
2. Event236 op15 / selector1 -> clear UJ-enabled for the target actor.
3. Keep native O14/O15 shadowed so the victim-UJ disappearance fix remains.
4. At main+0x7ABE9C, preserve native true results. A native false is changed to
   true only at the exact three UJ-router callers and only for an actor whose
   MovesetPlus selector1 semantic is enabled.

P64F DOES NOT force state 0x87 or PlayAction700.
The native router must still choose its own state/action.

Build
-----
Push this repository to GitHub and run:
  Build NSC P64F UJ Semantic Bridge

Expected artifact:
  NSC-P64F-uj-semantic-bridge

Pinned exlaunch commit:
  229bbd6

Install
-------
Deploy BOTH files from the compiled artifact:
  atmosphere/contents/0100FA10190A0000/exefs/main
  atmosphere/contents/0100FA10190A0000/exefs/subsdk9

Keep the current P33A Sorted=0 Tobi CPK and current ROMFS params unchanged.
Do not combine this subsdk9 with another experimental ExeFS build.

Expected startup marker
-----------------------
[NSC:P64F] READY ... semantic_bridge=1 ... gameplay_mutation=semantic_gate_only ...

Canonical single-session test
-----------------------------
1. Fresh boot.
2. Tobi (already awakened from battle start): press XA once.
   EXPECTED: ordinary jutsu stays ordinary.
3. Tobi: press XXA once.
   Watch whether route diverges from XA.
4. If UJ startup begins, let it run completely and note whether Kamui cinematic
   handoff/return succeeds or stalls. Handoff is a separate acceptance level.
5. Let a vanilla enemy UJ hit Tobi once.
   EXPECTED: Tobi remains visible/playable after cinematic.
6. Optional control: vanilla Kakashi normal UJ once.
7. Close emulator and preserve the full fresh Uzuy log.

Decision matrix
---------------
A) XA=445 and XXA reaches native UJ route/state 0x87/PlayAction700:
   P64F semantic bridge is validated. Move to Kamui cinematic handoff only.

B) XA=445 and XXA progresses farther but is blocked before UJ because Tobi is
   already awakened:
   selector1 backend is fixed; next functional delta is the data-driven
   OugiAwakeningParam membership consumer.

C) XA also turns into UJ:
   FAIL. The consumer context is too broad. Revert P64F; do not ship it.

D) XXA still exactly 445 and no P64F UJ_SEM_GATE semantic=1 is observed:
   semantic Event236 timing/actor targeting did not reach this consumer.

E) XXA still 445 but UJ_SEM_GATE shows semantic=1 ret=1:
   this selector1 consumer is not sufficient; inspect the next native predicate,
   without returning to selector8/F58/global-force experiments.

Regression blockers
-------------------
- enemy disappears / becomes unhittable
- Tobi disappears after victim UJ
- action148 chakra-charge loop
- repeated charge SFX
- global UJ always-on
- XA incorrectly becomes UJ
- HUD/input regression

Markers
-------
[NSC:P64F] UJ_SEM_SET ... enabled=1/0
[NSC:P64F] UJ_SEM_GATE ... native=... semantic=... ret=...
[NSC:P59A] PLAY_CALL ... index=445/700
[NSC:P63A] UJ_F58 ...
