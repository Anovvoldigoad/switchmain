# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R107

## Baseline
- Naruto x Boruto Ultimate Ninja STORM CONNECTIONS Switch v1.70
- Program ID: `0100FA10190A0000`
- main Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
- paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
- restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
- exlaunch pinned commit: `229bbd6`

## Locked architecture
- Generic/data-driven custom compatibility; no gameplay hardcode for fixture char281.
- Required Tobi UJ graph: `700 -> 707 -> 708 -> 710 -> cinematic`.
- 708 is required and must not be globally suppressed.
- P50 victim-safe Event236 shadows remain mandatory.
- P89 semantic + generated-membership admission bridge remains mandatory.
- Never force action700/708/710 or write E94/F58/BDA4/BDC8/EA4 speculatively.
- Trampoline capacity is tight; P100B proved a many-hook sweep can exhaust exlaunch allocator.

## P100C artifact audit
Uploaded compiled P100C artifact passed its internal SHA256SUMS verification.
- compiled subsdk9 SHA256: `452ccc58acb1e0937b4c2deb735a6dc27e9a316382cf34d227cf5ec4dbff4518`
- paired main hash: baseline PASS
- restore main hash: baseline PASS
- main/subsdk9 identify as Nintendo Switch NSO.

## P100C runtime conclusion — oracle hypothesis falsified
- P100C boots and reaches READY with one new trampoline.
- Vanilla control reaches native PlayAction710 from caller `main+0x7E6EC8`.
- Custom fixture reaches native 707->708 from caller `main+0x7725D0`, then later state125 cleanup and 261/74; no custom 710.
- No P100C ORACLE/ROUTE13 marker occurs in the full runtime log.
- Byte audit of the exact paired main explains this: `0x7E6A98 CBZ W8,0x7E6BB4` bypasses the five `0x64942C` calls when W8==0. Therefore helper `0x64942C` is not a mandatory action710 choke point. P100C is retired as diagnosis.

## New event-driven synthesis
The custom action708 is the loop phase. Resource semantics identify Event236 opcode23 (`me_play_action`) as the data-driven action transition mechanism for the loop END action (`SPSKILL_1_END`). Existing P50 already ports opcode23 through `HandleActionAnimation`; it is not shadow/no-op.

However log44 contains no Event236 `op=23` while the custom attacker is in action708. Instead:
1. custom enters 708 normally;
2. `SW_MTOB_XH` condition event executes while action708 is still alive;
3. very shortly afterward state125 is requested/committed;
4. cleanup leads to action261 then 74.

This supports a functional candidate: state125 cleanup may preempt action708 before its own data-driven op23 END transition can execute.

## P101A functional candidate — event-driven 708 END guard
Parent: P96A. P100C is not installed.

P101A adds exactly one whole-function trampoline at the previously boot-proven state request implementation `main+0x7A89A4`.

Guard rejects native state125 (`return 0`) only when ALL are true:
- valid actor identity;
- requested state == 125;
- current action == 708;
- semantic UJ latch active;
- generated OugiAwakening membership true;
- Event236 op23 has not yet been observed for this UJ attempt;
- EA4 <= `0x3000` safety window.

P101A modifies the existing semantic-control bitset with an op23-seen bit:
- reset only when semantic UJ transitions from disabled to enabled;
- clear when semantic UJ is disabled;
- set immediately before P50 handles Event236 opcode23 during semantic member action708.

Once op23 is seen, state125 immediately fails open. If op23 never appears, EA4 > `0x3000` also fails open and allows native cleanup, preventing indefinite action708 trapping.

P101A does NOT:
- force action710 or 708;
- rewrite action memory;
- write E94/E9C/BDA4/BDC8/EA4;
- restore raw native Event236;
- alter victim visibility shadow;
- branch on char281.

## Expected runtime markers
- `[NSC:P101A] READY ... probe=1`
- `[NSC:P101A] HOLD125 ... action=708 ... op23_seen=0 ...`
- desired: `[NSC:P101A] OP23 ... text=...END...`
- existing P50 should then log action-name resolution and PlayAction if the END action resolves.
- desired strongest proof: custom PlayAction710 / action708->710 followed by cinematic.
- safety fallback: `[NSC:P101A] PASS125 ... ea4>00003000 ...` if op23 never occurs.

## Test protocol
One functional run is enough:
1. Boot and verify P101A READY.
2. Use Tobi custom UJ and observe whether cinematic now triggers.
3. Also perform one victim-of-enemy-UJ regression if possible to ensure P50 victim safety remains intact.
4. Save log and compiled artifact.

If custom reaches 710/cinematic, immediately move to regression validation and retire broad UJ tracing.
If HOLD125 occurs but op23 still never appears and PASS125 eventually fires, this candidate is falsified cleanly without an infinite hang.
