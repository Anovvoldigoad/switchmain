# NSC2Switch MASTER CHECKPOINT — 2026-09-25 R119

## Locked target
- Storm Connections Switch v1.70
- Program ID `0100FA10190A0000`
- main Build ID `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256 `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256 `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pin `229bbd6`

## P107A runtime result
P107A exact `125 -> 137` bridge is a PARTIAL PASS:
- custom action708 reaches native PlayAction710 from `0x7E6EC8`;
- cinematic begins;
- other jutsu remain safe and victim-UJ safety remains safe.

But own-UJ lifecycle is broken:
- no UJ voice/audio;
- Kamui stage appears mixed with battle stage;
- enemy disappears during/after own UJ;
- Tobi is uncontrollable afterward;
- custom never follows the normal observed 711/712/713 continuation and falls through later cleanup.

At PlayAction710 under P107A, custom reaches state137 with stale setup context
(E98=63 and BDA4=1), unlike native successful UJ where state136 matures before
state137/710.

## Static state table proof
Pinned v1.70 state table base resolves to `main+0x205AAF8`, stride `0x20`:
- state125 record first qword = `0x4C0`;
- state136 = `0x518`;
- state137 = `0x520`.

Pinned runtime actor vtable family `main+0x201BF58` relocations:
- +0x4C0 -> `main+0x7DDD94`;
- +0x518 -> `main+0x7E47B8`;
- +0x520 -> `main+0x7E64D4`.

`main+0x7E47B8` (+0x518/state136 controller) contains:
- native action707/708 corridor;
- PlayAction136 participant setup at `0x7E54A0/0x7E54B0`;
- participant action138 at `0x7E5504`;
- participant action137 at `0x7E5570`.

`main+0x7E64D4` (+0x520/state137 controller) contains native action710 producer
at `0x7E6EA8/0x7E6EC4`.

## Source-event corroboration
The custom moveset source contains a post-loop END/DEMO transition using
Event236 opcode23 with state/action parameter136 before the Kamui demo stage.
The P107A runtime jumps to state137/710 without reconstructing that setup phase.

## P108A functional candidate
Retire P107A direct `125 -> 137` mapping.
On the same exact proven cleanup fingerprint only, map `125 -> 136` through the
native state-request API `main+0x7A89A4`.

Do not write E94/E9C/BDA fields directly. Let native commit state136, native
+0x518 setup controller run, and native state137/+0x520 produce 710.

Guard remains:
- side0 + semantic UJ + generated membership;
- caller `0x7EB28C`, request125, arg2=1,arg3=0;
- action708;
- E94=63,E98=136,E9C=0;
- BDA4=1,BDA8=0,BDC8=0.

## Independent Event236 parity gaps
Do not confuse these with the state bridge:
- opcode26 is `me_play_voice_string` in UltimateStormAPI and is still shadow/no-op on Switch, explaining missing voice;
- opcode14 old Switch helper is known unsafe and must NOT be restored;
- opcode12 remains victim-safe shadow;
- StageMove has historical partial parity and must be revisited only after state136 lifecycle is validated.

## P108A decision
Primary test is Tobi own UJ once, then one victim-UJ regression.
- If 136 -> native 137 -> 710 and post-UJ lifecycle improves: lock P108 state bridge, then port op26 audio separately.
- If 136 never reaches137/710: inspect only +0x518 first-difference; do not return to state125/261/74/gate12240.
