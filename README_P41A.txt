NSC2Switch P41A — CONDITION517 SPLIT BANK + EVENT121 SELF PARITY

Parent: P40A runtime result on uzuy_log(20).txt.

LOCKED P40 RESULT
- Naruto enemy UJ: PASS; Tobi no longer disappears.
- StageMove: PASS.
- Awakening: FAIL/unavailable.
- Kamui: FAIL/stuck before normal UJ handoff.
- EVT13_AWAKE: 0.
- OUGI_CORE: 0.
- Event121: 73 total; 72 SW_MTOB_XH records used p2=1 (SELF in UltimateStormAPI semantics).
- P40 O14 +0x12A24 candidate produced non-boolean reads, so P41A returns O14 to the P38A hardware-safe shadow baseline.

NEW ROOT-CAUSE PROOF PORTED INTO P41A MAIN
The current P40 restore main had fallen back to the vanilla native condition-manager geometry:
- condition getter accepted only IDs through 511;
- condition-name loops stopped at 512;
- no five-record high bank at 0x21616C8.

Historical hardware-stable R9A/R17 evidence proved the Switch v1.70 native architecture for custom conditions:
- total condition descriptors = 517;
- manager low table = main+0x20736C8;
- high bank = main+0x21616C8;
- getter uses split-bank bit9 rule, not one contiguous replacement manager;
- condition name loops use 0x205 (517);
- a five-record DT_INIT relocator fixes the high-bank name pointers.

P41A ports ONLY that proven condition subsystem onto the current P40 restore main:
1. Native count/bounds 512 -> 517 at verified sites.
2. Native split-bank getter restored using the verified R3/R9A instruction body.
3. Five native descriptor records installed at main+0x21616C8 with CURRENT names:
   SW_MTOB_XH
   SW_MTOB_ST
   YXNQ_MTOB
   SW_MTOB_BREAK
   WC_MTOB_BREAK
4. DT_INIT uses only the 36-byte five-record name-pointer relocator at main+0x12F5FD0.
5. The historical old Event236 trampoline after that relocator is NOT restored.
6. No MTOB->2TOB alias is used.
7. Old Ougi patches, char donor aliases, legacy custom-ID bounds and unrelated R3 main deltas are excluded.

Generated active main:
  p41_main/atmosphere/contents/0100FA10190A0000/exefs/main
  SHA256 = 407ff7247a2c70941c05eb2cdfbd65a2a25fffc247845274b096ed0b5aee6ae7
Build ID remains 48ece454b61412b9fb46fab2be3f5ef7b2804f39.

P41A SUBSDK9 GAMEPLAY DELTA
- O14: P38A-safe shadow/no-op.
- Event121 for generic custom actors (charID >280 && <0x1000):
  signed int16 event+0x26 == 1 -> SELF target using exact native helper chain
  0x7630FC -> 0x777758 -> 0x7630FC -> 0x776014.
- Resolver result <=0 fails closed and is NOT applied to enemy.
- Event121 p2 !=1 remains exact native Switch callback.
- No condition-name alias, Tobi/281/donor/COND_2DNZ mapping, or awakening force.
- Event13 and Ougi Core include RAW entry markers before actor-identity filtering.

UNCHANGED / DO NOT REGRESS
- P33A Sorted=0 CPK/resource layer.
- Generic custom Event236 dispatcher.
- O2 StageMove.
- O12 remains shadow.
- O15 remains no-op.
- O18 remains shadow; no exact current handler is guessed.
- 0x7E13E4 / 0x7E1404 / 0x7E1408 remain untouched.

DEPLOYMENT
Use BOTH files produced by the CI artifact:
  atmosphere/contents/0100FA10190A0000/exefs/main
  atmosphere/contents/0100FA10190A0000/exefs/subsdk9
Keep the current P33A Sorted=0 CPK, loose charicon and current RomFS params unchanged.

HARDWARE TEST ORDER
1. Fresh boot. READY must contain cond517=1 splitbank=1 evt121_self=1 ctrl14_shadow=1.
2. Tobi vs Naruto slot1: receive enemy UJ once. Tobi must remain present/playable.
3. From normal state attempt awakening several times.
4. Trigger Kamui once and leave the stuck/capture state briefly.
5. If another action normally releases the victim, use it once.
6. Trigger StageMove once.
7. Send the complete fresh Uzuy log.

DECISION GATES
- EVT121_SELF resolved 512..516 and executed=1: native custom condition bank is live.
- resolved=0: reject condition-main integration before changing gameplay.
- custom condition executes and EVT13_RAW/AWAKE begins appearing: condition integration opened the awakening path; inspect Event13 result before any force.
- custom condition executes but awakening still has no EVT13_RAW: next target is the exact specialCond/eligibility consumer, not Event13 itself.
- Kamui starts reaching OUGI_RAW/OUGI_CORE: condition integration opened the missing UJ handoff.
- Kamui still has no OUGI_RAW: trace the unique upstream caller/gate before 0x7E0F58; do not revive 0x7E13E4/0x7E1404 guesses.
- Naruto victim-UJ or StageMove regresses: stop on this build and inspect the new Event121/condition activity.
